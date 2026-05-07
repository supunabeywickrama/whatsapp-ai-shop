'use client';

import { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useToken } from '@/hooks/useToken';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogClose,
} from '@/components/ui/dialog';

interface Brand { id: string; name: string; logo_url: string | null }
const EMPTY: Omit<Brand, 'id'> = { name: '', logo_url: null };

export default function BrandsPage() {
  const token = useToken();
  const [brands, setBrands] = useState<Brand[]>([]);
  const [open, setOpen]     = useState(false);
  const [editing, setEditing] = useState<Brand | null>(null);
  const [form, setForm]     = useState<Omit<Brand, 'id'>>(EMPTY);
  const [busy, setBusy]     = useState(false);
  const [error, setError]   = useState<string | null>(null);

  async function load() { setBrands(await api<Brand[]>('/api/brands')); }
  useEffect(() => { load(); }, []);

  function openAdd() {
    setEditing(null); setForm(EMPTY); setError(null); setOpen(true);
  }
  function openEdit(b: Brand) {
    setEditing(b); setForm({ name: b.name, logo_url: b.logo_url }); setError(null); setOpen(true);
  }

  async function save() {
    setBusy(true); setError(null);
    try {
      if (editing) {
        await api(`/api/brands/${editing.id}`, { method: 'PUT', body: JSON.stringify(form) }, token ?? undefined);
      } else {
        await api('/api/brands', { method: 'POST', body: JSON.stringify(form) }, token ?? undefined);
      }
      setOpen(false); load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally { setBusy(false); }
  }

  async function remove(id: string) {
    if (!confirm('Delete this brand?')) return;
    await api(`/api/brands/${id}`, { method: 'DELETE' }, token ?? undefined);
    load();
  }

  return (
    <div className="container py-8 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Brands</h1>
          <p className="text-muted-foreground text-sm mt-1">{brands.length} brands</p>
        </div>
        <Button onClick={openAdd}><Plus className="h-4 w-4" /> Add brand</Button>
      </div>

      <div className="rounded-2xl border overflow-hidden">
        {brands.length === 0 && (
          <p className="text-center py-10 text-muted-foreground">No brands yet.</p>
        )}
        {brands.map((b) => (
          <div key={b.id} className="flex items-center justify-between px-5 py-3 border-b last:border-b-0 hover:bg-muted/30 transition-colors">
            <span className="font-medium text-sm">{b.name}</span>
            <div className="flex gap-1">
              <Button size="icon" variant="ghost" onClick={() => openEdit(b)}>
                <Pencil className="h-4 w-4" />
              </Button>
              <Button size="icon" variant="ghost" onClick={() => remove(b.id)}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit brand' : 'Add brand'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name *</label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Samsung" />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <DialogClose asChild><Button variant="outline">Cancel</Button></DialogClose>
            <Button onClick={save} disabled={busy}>{busy ? 'Saving…' : 'Save'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
