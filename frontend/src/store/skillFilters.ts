import { create } from 'zustand';
import { SkillType, SkillStatus, SkillRuntime } from '@/types';

interface SkillFiltersState {
  search: string;
  type: SkillType | 'all';
  status: SkillStatus | 'all';
  runtime: SkillRuntime | 'all';
  setSearch: (search: string) => void;
  setType: (type: SkillType | 'all') => void;
  setStatus: (status: SkillStatus | 'all') => void;
  setRuntime: (runtime: SkillRuntime | 'all') => void;
  resetFilters: () => void;
}

export const useSkillFilters = create<SkillFiltersState>((set) => ({
  search: '',
  type: 'all',
  status: 'all',
  runtime: 'all',
  setSearch: (search) => set({ search }),
  setType: (type) => set({ type }),
  setStatus: (status) => set({ status }),
  setRuntime: (runtime) => set({ runtime }),
  resetFilters: () => set({ search: '', type: 'all', status: 'all', runtime: 'all' }),
}));
