import { formatDistanceToNow, format } from 'date-fns';

export const formatRelativeTime = (date: string | Date): string => {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
};

export const formatDate = (date: string | Date, formatStr: string = 'yyyy-MM-dd HH:mm:ss'): string => {
  return format(new Date(date), formatStr);
};

export const formatShortDate = (date: string | Date): string => {
  return format(new Date(date), 'MMM dd, yyyy');
};
