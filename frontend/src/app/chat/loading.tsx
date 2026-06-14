export default function ChatLoading() {
  return (
    <div className="max-w-4xl mx-auto p-6 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6" />
      <div className="space-y-4">
        <div className="h-16 bg-gray-100 rounded" />
        <div className="h-16 bg-gray-100 rounded" />
      </div>
    </div>
  );
}
