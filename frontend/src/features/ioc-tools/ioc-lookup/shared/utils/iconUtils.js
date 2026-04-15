/**
 * Loads a service icon by name with fallback to default icon.
 * Returns the image source or null if no icon can be loaded.
 */
export function getServiceIcon(iconName) {
  if (!iconName || iconName === 'default_icon') {
    try {
      return require('../icons/default_icon.png');
    } catch (e) {
      return null;
    }
  }

  try {
    return require(`../icons/${iconName}.png`);
  } catch (e) {
    try {
      return require('../icons/default_icon.png');
    } catch (e2) {
      return null;
    }
  }
}
