import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import AlternateEmailIcon from '@mui/icons-material/AlternateEmail';
import LanIcon from '@mui/icons-material/Lan';
import LinkIcon from '@mui/icons-material/Link';
import PublicIcon from '@mui/icons-material/Public';

export const IOC_CATEGORIES = [
  {
    title: 'Domains',
    type: 'domain',
    dataKey: 'domains',
    icon: PublicIcon
  },
  {
    title: 'IP addresses',
    type: 'ipv4',
    dataKey: 'ips',
    icon: LanIcon
  },
  {
    title: 'URLs',
    type: 'url',
    dataKey: 'urls',
    icon: LinkIcon
  },
  {
    title: 'Email addresses',
    type: 'email',
    dataKey: 'emails',
    icon: AlternateEmailIcon
  },
  {
    title: 'MD5 hashes',
    type: 'md5',
    dataKey: 'md5',
    icon: InsertDriveFileIcon
  },
  {
    title: 'SHA1 hashes',
    type: 'sha1',
    dataKey: 'sha1',
    icon: InsertDriveFileIcon
  },
  {
    title: 'SHA256 hashes',
    type: 'sha256',
    dataKey: 'sha256',
    icon: InsertDriveFileIcon
  }
];
