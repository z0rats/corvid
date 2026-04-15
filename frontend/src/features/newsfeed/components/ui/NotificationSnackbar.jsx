import AppSnackbar from '../../../../core/components/ui/AppSnackbar';

export default function NotificationSnackbar({ open, message, severity, onClose }) {
  return <AppSnackbar open={open} message={message} severity={severity} onClose={onClose} />;
}
