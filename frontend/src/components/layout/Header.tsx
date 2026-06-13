export default function Header() {
  return (
    <header className="border-b">
      <div className="mx-auto max-w-6xl px-6 py-4 flex justify-between">
        <h1 className="font-bold text-xl">NeedNow AI</h1>

        <nav className="flex gap-4">
          <a href="/">Home</a>
          <a href="/cart">Cart</a>
          <a href="/history">History</a>
        </nav>
      </div>
    </header>
  );
}
