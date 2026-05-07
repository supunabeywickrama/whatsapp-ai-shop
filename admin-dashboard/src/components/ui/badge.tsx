import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default:     'bg-primary/15 text-primary',
        secondary:   'bg-secondary text-secondary-foreground',
        destructive: 'bg-destructive/15 text-destructive',
        outline:     'border text-foreground',
        success:     'bg-green-500/15 text-green-600 dark:text-green-400',
        warning:     'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
