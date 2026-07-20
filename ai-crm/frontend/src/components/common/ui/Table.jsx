import React from 'react';
import { cn } from '@/utils/helpers';

export const Table = ({ className, children, ...props }) => (
  <div className="w-full overflow-auto rounded-lg border shadow-sm">
    <table className={cn('w-full caption-bottom text-sm', className)} {...props}>
      {children}
    </table>
  </div>
);

export const TableHeader = ({ className, children, ...props }) => (
  <thead className={cn('bg-muted/50', className)} {...props}>
    {children}
  </thead>
);

export const TableBody = ({ className, children, ...props }) => (
  <tbody className={cn('[&_tr:last-child]:border-0', className)} {...props}>
    {children}
  </tbody>
);

export const TableFooter = ({ className, children, ...props }) => (
  <tfoot className={cn('bg-muted/50 font-medium', className)} {...props}>
    {children}
  </tfoot>
);

export const TableRow = ({ className, children, ...props }) => (
  <tr
    className={cn(
      'border-b transition-colors hover:bg-muted/30',
      className
    )}
    {...props}
  >
    {children}
  </tr>
);

export const TableHead = ({ className, children, ...props }) => (
  <th
    className={cn(
      'h-12 px-4 text-left align-middle font-semibold text-muted-foreground',
      className
    )}
    {...props}
  >
    {children}
  </th>
);

export const TableCell = ({ className, children, ...props }) => (
  <td
    className={cn('p-4 align-middle', className)}
    {...props}
  >
    {children}
  </td>
);

export default Table;
