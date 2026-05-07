export default function InventoryPage() {
  return (
    <main className="container py-12">
      <h1 className="text-3xl font-bold mb-2">Inventory</h1>
      <p className="text-muted-foreground mb-8">
        Add, edit, and delete products. CSV import. Stock toggle.
      </p>
      <div className="rounded-2xl border bg-card p-8 text-muted-foreground">
        Inventory table coming in Phase 2 — wires up to{' '}
        <code className="text-foreground">GET /api/products</code>.
      </div>
    </main>
  );
}
