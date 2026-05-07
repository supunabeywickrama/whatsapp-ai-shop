'use client';

import { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useToken } from '@/hooks/useToken';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogClose,
} from '@/components/ui/dialog';
import { Select } from '@/components/ui/select';

interface Category { id: string; name: string }
interface Brand    { id: string; name: string }
interface Product {
  id: string; sku: string; title: string; condition: string;
  price: number; discounted_price: number | null; stock_qty: number;
  is_active: boolean; category_id: string; brand_id: string | null;
}

const EMPTY: Omit<Product, 'id'> = {
  sku: '', title: '', condition: 'new', price: 0,
  discounted_price: null, stock_qty: 0, is_active: true,
  category_id: '', brand_id: null,
};

export default function InventoryPage() {
  const token = useToken();
  const [products, setProducts]   = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands]       = useState<Brand[]>([]);
  const [q, setQ]                 = useState('');
  const [open, setOpen]           = useState(false);
  const [editing, setEditing]     = useState<Product | null>(null);
  const [form, setForm]           = useState<Omit<Product, 'id'>>(EMPTY);
  const [busy, setBusy]           = useState(false);
  const [error, setError]         = useState<string | null>(null);

  async function load() {
    const [p, c, b] = await Promise.all([
      api<Product[]>(`/api/products${q ? `?q=${encodeURIComponent(q)}` : ''}`),
      api<Category[]>('/api/categories'),
      api<Brand[]>('/api/brands'),
    ]);
    setProducts(p); setCategories(c); setBrands(b);
  }

  useEffect(() => { load(); }, [q]); // eslint-disable-line

  function openAdd() {
    setEditing(null);
    setForm({ ...EMPTY, category_id: categories[0]?.id ?? '' });
    setError(null); setOpen(true);
  }

  function openEdit(p: Product) {
    setEditing(p);
    setForm({ ...p });
    setError(null); setOpen(true);
  }

  async function save() {
    setBusy(true); setError(null);
    try {
      if (editing) {
        await api(`/api/products/${editing.id}`, {
          method: 'PUT', body: JSON.stringify(form),
        }, token ?? undefined);
      } else {
        await api('/api/products', { method: 'POST', body: JSON.stringify(form) }, token ?? undefined);
      }
      setOpen(false); load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    if (!confirm('Delete this product?')) return;
    await api(`/api/products/${id}`, { method: 'DELETE' }, token ?? undefined);
    load();
  }

  const conditionColor: Record<string, 'success' | 'warning' | 'secondary'> = {
    new: 'success', used: 'warning', refurbished: 'secondary',
  };

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Inventory</h1>
          <p className="text-muted-foreground text-sm mt-1">{products.length} products</p>
        </div>
        <Button onClick={openAdd}>
          <Plus className="h-4 w-4" /> Add product
        </Button>
      </div>

      <div className="mb-4">
        <Input
          placeholder="Search by name or SKU…"
          value={q} onChange={(e) => setQ(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="rounded-2xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {['SKU', 'Title', 'Condition', 'Price (Rs)', 'Stock', 'Status', ''].map((h) => (
                <th key={h} className="text-left px-4 py-3 font-medium text-muted-foreground">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-10 text-muted-foreground">No products yet.</td>
              </tr>
            )}
            {products.map((p) => (
              <tr key={p.id} className="border-t hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3 font-mono text-xs">{p.sku}</td>
                <td className="px-4 py-3 font-medium">{p.title}</td>
                <td className="px-4 py-3">
                  <Badge variant={conditionColor[p.condition] ?? 'secondary'}>{p.condition}</Badge>
                </td>
                <td className="px-4 py-3">
                  {p.discounted_price
                    ? <><span className="line-through text-muted-foreground mr-2">{Number(p.price).toLocaleString()}</span>{Number(p.discounted_price).toLocaleString()}</>
                    : Number(p.price).toLocaleString()}
                </td>
                <td className="px-4 py-3">{p.stock_qty}</td>
                <td className="px-4 py-3">
                  <Badge variant={p.is_active ? 'success' : 'secondary'}>
                    {p.is_active ? 'Active' : 'Hidden'}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" onClick={() => openEdit(p)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button size="icon" variant="ghost" onClick={() => remove(p.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add / Edit Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit product' : 'Add product'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">SKU *</label>
                <Input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="SAMS-CHG-25W" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Condition</label>
                <Select value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
                  <option value="new">New</option>
                  <option value="used">Used</option>
                  <option value="refurbished">Refurbished</option>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Title *</label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Samsung 25W USB-C Fast Charger" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Price (Rs) *</label>
                <Input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Discounted price</label>
                <Input type="number" value={form.discounted_price ?? ''} onChange={(e) => setForm({ ...form, discounted_price: e.target.value ? Number(e.target.value) : null })} placeholder="optional" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Stock qty</label>
                <Input type="number" value={form.stock_qty} onChange={(e) => setForm({ ...form, stock_qty: Number(e.target.value) })} />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Category *</label>
                <Select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                  <option value="">— select —</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Brand</label>
                <Select value={form.brand_id ?? ''} onChange={(e) => setForm({ ...form, brand_id: e.target.value || null })}>
                  <option value="">— none —</option>
                  {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                </Select>
              </div>
              <div className="flex items-end pb-1">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                  Active (visible to AI)
                </label>
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button onClick={save} disabled={busy}>
              {busy ? 'Saving…' : 'Save product'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
