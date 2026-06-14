export default function CartLoading() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-8 animate-pulse">
      <div className="h-8 w-40 bg-slate-200 rounded mb-6" />
      <div className="space-y-3">
        <div className="h-16 bg-slate-100 rounded-lg" />
        <div className="h-16 bg-slate-100 rounded-lg" />
        <div className="h-16 bg-slate-100 rounded-lg" />
      </div>
    </div>
  );
}
