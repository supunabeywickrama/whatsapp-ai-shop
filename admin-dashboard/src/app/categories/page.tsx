'use client';

import { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2, ChevronRight } from 'lucide-react';
import { api } from '@/lib/api';
import { useToken } from '@/hooks/useToken';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter, DialogClose,
} from '@/components/ui/dialog';

interface Category {
  id: string; name: string; parent_id: string | null;
  icon_url: string | null; sort_order: number;
}

const EMPTY: Omit<Category, 'id'> = { name: '', parent_id: null, icon_url: null, sort_order: 0 };

export default function CategoriesPage() {
  const token = useToken();
  const [categories, setCategories] = useState<Category[]>([]);
  const [open, setOpen]     = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [form, setForm]     = useState<Omit<Category, 'id'>>(EMPTY);
  const [busy, setBusy]     = useState(false);
  const [error, setError]   = useState<string | null>(null);

  async function load() {
    setCategories(await api<Category[]>('/api/categories'));
  }
  useEffect(() => { load(); }, []);

  const roots  = categories.filter((c) => !c.parent_id);
  const children = (parentId: string) => categories.filter((c) => c.parent_id === parentId);

  function openAdd(parentId?: string) {
    setEditing(null);
    setForm({ ...EMPTY, parent_id: parentId ?? null });
    setError(null); setOpen(true);
  }

  function openEdit(c: Category) {
    setEditing(c);
    setForm({ name: c.name, parent_id: c.parent_id, icon_url: c.icon_url, sort_order: c.sort_order });
    setError(null); setOpen(true);
  }

  async function save() {
    setBusy(true); setError(null);
    try {
      if (editing) {
        await api(`/api/categories/${editing.id}`, { method: 'PUT', body: JSON.stringify(form) }, token ?? undefined);
      } else {
        await api('/api/categories', { method: 'POST', body: JSON.stringify(form) }, token ?? undefined);
      }
      setOpen(false); load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally { setBusy(false); }
  }

  async function remove(id: string) {
    if (!confirm('Delete this category? Products in it will be unlinked.')) return;
    await api(`/api/categories/${id}`, { method: 'DELETE' }, token ?? undefined);
    load();
  }

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Categories</h1>
          <p className="text-muted-foreground text-sm mt-1">{categories.length} total</p>
        </div>
        <Button onClick={() => openAdd()}>
          <Plus className="h-4 w-4" /> Add category
        </Button>
      </div>

      <div className="rounded-2xl border overflow-hidden">
        {roots.length === 0 && (
          <p className="text-center py-10 text-muted-foreground">No categories yet.</p>
        )}
        {roots.map((root) => (
          <div key={root.id}>
            <div className="flex items-center justify-between px-5 py-3 border-b hover:bg-muted/30 transition-colors bg-muted/10">
              <span className="font-semibold text-sm">{root.name}</span>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => openAdd(root.id)}>
                  <Plus className="h-3 w-3 mr-1" /> Sub
                </Button>
                <Button size="icon" variant="ghost" onClick={() => openEdit(root)}>
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button size="icon" variant="ghost" onClick={() => remove(root.id)}>
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </div>
            </div>
            {children(root.id).map((child) => (
              <div key={child.id} className="flex items-center justify-between px-8 py-2.5 border-b last:border-b-0 hover:bg-muted/20 transition-colors">
                <span className="flex items-center gap-2 text-sm text-muted-foreground">
                  <ChevronRight className="h-3 w-3" /> {child.name}
                </span>
                <div className="flex gap-1">
                  <Button size="icon" variant="ghost" onClick={() => openEdit(child)}>
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => remove(child.id)}>
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit category' : 'Add category'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name *</label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Chargers" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Parent category</label>
              <Select value={form.parent_id ?? ''} onChange={(e) => setForm({ ...form, parent_id: e.target.value || null })}>
                <option value="">— top level —</option>
                {categories
                  .filter((c) => !c.parent_id && c.id !== editing?.id)
                  .map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Sort order</label>
              <Input type="number" value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })} />
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
