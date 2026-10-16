import Typography from '@mui/material/Typography';

/** A feature page's title plus an optional one-line description, above its form. */
export default function PageHeader({ title, description }) {
  return (
    <>
      <Typography variant="h5" component="h1" sx={{ mb: description ? 1 : 2 }}>{title}</Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {description}
        </Typography>
      )}
    </>
  );
}
