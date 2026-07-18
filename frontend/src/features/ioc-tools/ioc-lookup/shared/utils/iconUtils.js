const icons = import.meta.glob('../icons/*.png', { eager: true, import: 'default' });

function iconSrc(iconName) {
  return icons[`../icons/${iconName}.png`] ?? null;
}

/**
 * Loads a service icon by name with fallback to default icon.
 * Returns the image source or null if no icon can be loaded.
 */
export function getServiceIcon(iconName) {
  if (!iconName || iconName === 'default_icon') {
    return iconSrc('default_icon');
  }

  return iconSrc(iconName) ?? iconSrc('default_icon');
}
