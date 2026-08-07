// Minimal hand-rolled EXIF/TIFF parser — covers the fields OSINT work actually cares about
// (camera, timestamps, GPS) across the formats that can actually carry EXIF on the web: JPEG,
// PNG (eXIf chunk), WebP (EXIF chunk, only present in the extended/VP8X container), and
// standalone TIFF. No XMP/IPTC/maker-notes, no third-party library, per this project's
// dependency-minimization convention. Every format ultimately wraps the same raw TIFF payload,
// so only the "find where that payload starts" step differs per container. Loaded via
// importScripts() in background.js (service worker) and a plain <script> tag in sidepanel.html
// — must stay a classic (non-module) script so both work.

const EXIF_TAGS = {
  0x0100: 'ImageWidth',
  0x0101: 'ImageLength',
  0x010f: 'Make',
  0x0110: 'Model',
  0x0112: 'Orientation',
  0x0131: 'Software',
  0x0132: 'DateTime',
  0x829a: 'ExposureTime',
  0x829d: 'FNumber',
  0x8822: 'ExposureProgram',
  0x8827: 'ISOSpeedRatings',
  0x9003: 'DateTimeOriginal',
  0x9004: 'DateTimeDigitized',
  0x920a: 'FocalLength',
  0x9209: 'Flash',
  0xa001: 'ColorSpace',
  0xa002: 'PixelXDimension',
  0xa003: 'PixelYDimension',
  0xa403: 'WhiteBalance',
  0xa434: 'LensModel',
};

const GPS_TAGS = {
  0x0001: 'GPSLatitudeRef',
  0x0002: 'GPSLatitude',
  0x0003: 'GPSLongitudeRef',
  0x0004: 'GPSLongitude',
  0x0005: 'GPSAltitudeRef',
  0x0006: 'GPSAltitude',
  0x000d: 'GPSSpeed',
  0x0011: 'GPSImgDirection',
  0x001d: 'GPSDateStamp',
};

const EXIF_IFD_POINTER = 0x8769;
const GPS_IFD_POINTER = 0x8825;
const TYPE_SIZES = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8 };

// --- Container readers: each finds pixel dimensions (best-effort) and where the raw TIFF/EXIF
// payload starts (tiffStart), or null if the format can't/doesn't carry one. ---

function readJpeg(view) {
  let dimensions = null;
  let tiffStart = null;
  let offset = 2;
  while (offset < view.byteLength - 4) {
    if (view.getUint8(offset) !== 0xff) break;
    const marker = view.getUint8(offset + 1);
    const length = view.getUint16(offset + 2);

    const isSof = marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc;
    if (isSof && offset + 9 <= view.byteLength) {
      dimensions = { height: view.getUint16(offset + 5), width: view.getUint16(offset + 7) };
    } else if (marker === 0xe1 && offset + 10 <= view.byteLength) {
      const sig = String.fromCharCode(...new Uint8Array(view.buffer, offset + 4, 6));
      if (sig === 'Exif\0\0') tiffStart = offset + 10;
    }
    if (marker === 0xda) break; // start of scan — no more markers before compressed data
    if (dimensions && tiffStart != null) break;
    offset += 2 + length;
  }
  return { dimensions, tiffStart };
}

function readPng(view) {
  let dimensions = null;
  let tiffStart = null;
  let offset = 8; // past the 8-byte PNG signature
  while (offset + 8 <= view.byteLength) {
    const length = view.getUint32(offset);
    const type = String.fromCharCode(
      view.getUint8(offset + 4),
      view.getUint8(offset + 5),
      view.getUint8(offset + 6),
      view.getUint8(offset + 7),
    );
    const dataStart = offset + 8;
    if (type === 'IHDR' && dataStart + 8 <= view.byteLength) {
      dimensions = { width: view.getUint32(dataStart), height: view.getUint32(dataStart + 4) };
    } else if (type === 'eXIf') {
      tiffStart = dataStart; // raw TIFF, no "Exif\0\0" prefix in PNG's eXIf chunk
    } else if (type === 'IDAT' || type === 'IEND') {
      break; // eXIf always precedes image data per spec — no point scanning further
    }
    offset = dataStart + length + 4; // skip chunk data + its trailing CRC
  }
  return { dimensions, tiffStart };
}

function readWebp(view) {
  let dimensions = null;
  let tiffStart = null;
  let offset = 12; // past 'RIFF' + size(4) + 'WEBP'
  while (offset + 8 <= view.byteLength) {
    const fourCC = String.fromCharCode(
      view.getUint8(offset),
      view.getUint8(offset + 1),
      view.getUint8(offset + 2),
      view.getUint8(offset + 3),
    );
    const size = view.getUint32(offset + 4, true); // RIFF chunk sizes are little-endian
    const dataStart = offset + 8;

    if (fourCC === 'VP8X' && dataStart + 10 <= view.byteLength) {
      // EXIF/XMP/ICC can only appear in the extended (VP8X) container, which conveniently also
      // carries plain-old width/height — so we never need the bit-packed VP8/VP8L frame headers.
      const width = 1 + (view.getUint8(dataStart + 4) | (view.getUint8(dataStart + 5) << 8) | (view.getUint8(dataStart + 6) << 16));
      const height = 1 + (view.getUint8(dataStart + 7) | (view.getUint8(dataStart + 8) << 8) | (view.getUint8(dataStart + 9) << 16));
      dimensions = { width, height };
    } else if (fourCC === 'EXIF') {
      tiffStart = dataStart;
      if (size >= 6) {
        const sig = String.fromCharCode(...new Uint8Array(view.buffer, dataStart, 6));
        if (sig === 'Exif\0\0') tiffStart = dataStart + 6; // some encoders keep the JPEG-style prefix
      }
    }
    offset = dataStart + size + (size % 2); // chunks are padded to an even byte count
  }
  return { dimensions, tiffStart };
}

function detectFormat(view) {
  if (view.byteLength >= 2 && view.getUint16(0) === 0xffd8) return 'jpeg';
  if (view.byteLength >= 8 && view.getUint32(0) === 0x89504e47 && view.getUint32(4) === 0x0d0a1a0a) return 'png';
  if (view.byteLength >= 12 && view.getUint32(0) === 0x52494646 && view.getUint32(8) === 0x57454250) return 'webp';
  if (view.byteLength >= 4) {
    const marker = view.getUint16(0, false);
    if ((marker === 0x4949 && view.getUint16(2, true) === 0x002a) || (marker === 0x4d4d && view.getUint16(2, false) === 0x002a)) {
      return 'tiff'; // standalone TIFF file — the whole file already *is* the payload we parse below
    }
  }
  return 'unsupported';
}

// --- Shared TIFF/IFD walking, used for the payload found by whichever container reader ran. ---

function readTag(view, tiffStart, littleEndian, entryOffset) {
  const tag = view.getUint16(entryOffset, littleEndian);
  const type = view.getUint16(entryOffset + 2, littleEndian);
  const count = view.getUint32(entryOffset + 4, littleEndian);
  const size = (TYPE_SIZES[type] || 1) * count;
  const valueOffset = size > 4 ? tiffStart + view.getUint32(entryOffset + 8, littleEndian) : entryOffset + 8;

  const readAt = (i) => {
    switch (type) {
      case 1:
      case 7:
        return view.getUint8(valueOffset + i);
      case 3:
        return view.getUint16(valueOffset + i * 2, littleEndian);
      case 4:
        return view.getUint32(valueOffset + i * 4, littleEndian);
      case 9:
        return view.getInt32(valueOffset + i * 4, littleEndian);
      case 5: {
        const num = view.getUint32(valueOffset + i * 8, littleEndian);
        const den = view.getUint32(valueOffset + i * 8 + 4, littleEndian);
        return den ? num / den : 0;
      }
      case 10: {
        const num = view.getInt32(valueOffset + i * 8, littleEndian);
        const den = view.getInt32(valueOffset + i * 8 + 4, littleEndian);
        return den ? num / den : 0;
      }
      default:
        return null;
    }
  };

  let value;
  if (type === 2) {
    const bytes = new Uint8Array(view.buffer, valueOffset, count);
    value = new TextDecoder().decode(bytes).replace(/\0+$/, '');
  } else if (count === 1) {
    value = readAt(0);
  } else {
    value = Array.from({ length: count }, (_, i) => readAt(i));
  }
  return { tag, value };
}

function readIFD(view, tiffStart, littleEndian, ifdOffset, tagMap, out) {
  const entryCount = view.getUint16(ifdOffset, littleEndian);
  const subIfdPointers = {};
  for (let i = 0; i < entryCount; i++) {
    const { tag, value } = readTag(view, tiffStart, littleEndian, ifdOffset + 2 + i * 12);
    if (tag === EXIF_IFD_POINTER || tag === GPS_IFD_POINTER) {
      subIfdPointers[tag] = tiffStart + value;
      continue;
    }
    const name = tagMap[tag];
    if (name) out[name] = value;
  }
  return subIfdPointers;
}

function dmsToDecimal(dms, ref) {
  if (!Array.isArray(dms) || dms.length !== 3) return null;
  const [d, m, s] = dms;
  let decimal = d + m / 60 + s / 3600;
  if (ref === 'S' || ref === 'W') decimal = -decimal;
  return decimal;
}

function parseTiffPayload(view, tiffStart) {
  const littleEndian = view.getUint16(tiffStart, false) === 0x4949;
  const firstIfdOffset = view.getUint32(tiffStart + 4, littleEndian);

  const exif = {};
  const gps = {};
  const pointers = readIFD(view, tiffStart, littleEndian, tiffStart + firstIfdOffset, EXIF_TAGS, exif);

  if (pointers[EXIF_IFD_POINTER]) {
    const subPointers = readIFD(view, tiffStart, littleEndian, pointers[EXIF_IFD_POINTER], EXIF_TAGS, exif);
    Object.assign(pointers, subPointers);
  }
  if (pointers[GPS_IFD_POINTER]) {
    readIFD(view, tiffStart, littleEndian, pointers[GPS_IFD_POINTER], GPS_TAGS, gps);
  }

  if (gps.GPSLatitude) exif.GPSLatitude = dmsToDecimal(gps.GPSLatitude, gps.GPSLatitudeRef);
  if (gps.GPSLongitude) exif.GPSLongitude = dmsToDecimal(gps.GPSLongitude, gps.GPSLongitudeRef);
  if (gps.GPSAltitude != null) exif.GPSAltitude = gps.GPSAltitudeRef === 1 ? -gps.GPSAltitude : gps.GPSAltitude;
  if (gps.GPSImgDirection != null) exif.GPSImgDirection = gps.GPSImgDirection;
  if (gps.GPSSpeed != null) exif.GPSSpeed = gps.GPSSpeed;
  if (gps.GPSDateStamp) exif.GPSDateStamp = gps.GPSDateStamp;

  return exif;
}

function parseImageExif(arrayBuffer) {
  const view = new DataView(arrayBuffer);
  const format = detectFormat(view);
  if (format === 'unsupported') return { format, dimensions: null, exif: null };

  let dimensions = null;
  let tiffStart = null;
  if (format === 'jpeg') ({ dimensions, tiffStart } = readJpeg(view));
  else if (format === 'png') ({ dimensions, tiffStart } = readPng(view));
  else if (format === 'webp') ({ dimensions, tiffStart } = readWebp(view));
  else if (format === 'tiff') tiffStart = 0; // the whole file is the TIFF payload

  if (tiffStart == null) return { format, dimensions, exif: null };

  const exif = parseTiffPayload(view, tiffStart);
  if (!dimensions && exif.ImageWidth && exif.ImageLength) {
    dimensions = { width: exif.ImageWidth, height: exif.ImageLength };
  }

  const hasData = Object.keys(exif).length > 0;
  return { format, dimensions, exif: hasData ? exif : null };
}

// Classic script (no `export`): consumed via importScripts() in the service worker and a
// plain <script> tag in sidepanel.html, both of which share this top-level scope.
