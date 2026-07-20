import clsx from 'clsx';

const Loading = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div
        className={clsx(
          'animate-spin rounded-full border-b-2 border-primary',
          sizes[size]
        )}
      />
    </div>
  );
};

const LoadingPage = () => {
  return (
    <div className="min-h-[400px] flex items-center justify-center">
      <Loading size="lg" />
    </div>
  );
};

const LoadingOverlay = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-card rounded-2xl p-8 flex flex-col items-center gap-4 border border-border/30 shadow-xl">
        <Loading size="lg" />
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  );
};

const Skeleton = ({ className, ...props }) => {
  return (
    <div
      className={clsx('animate-pulse rounded bg-muted', className)}
      {...props}
    />
  );
};

Loading.Page = LoadingPage;
Loading.Overlay = LoadingOverlay;
Loading.Skeleton = Skeleton;

export default Loading;
