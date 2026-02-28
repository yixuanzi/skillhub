import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  currentModule: string;
  setSidebarOpen: (open: boolean) => void;
  setCurrentModule: (module: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentModule: 'dashboard',
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentModule: (module) => set({ currentModule: module }),
}));
