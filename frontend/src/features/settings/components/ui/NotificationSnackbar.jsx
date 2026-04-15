import AppSnackbar from '../../../../core/components/ui/AppSnackbar';

export default function NotificationSnackbar({ notification, onClose }) {
  return (
    <AppSnackbar
      open={notification.open}
      message={notification.message}
      severity={notification.severity}
      onClose={onClose}
    />
  );
}
