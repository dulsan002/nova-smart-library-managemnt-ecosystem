/**
 * Tests for Badge component.
 */

import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/Badge';

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders as a span element', () => {
    render(<Badge>Status</Badge>);
    const el = screen.getByText('Status');
    expect(el.tagName).toBe('SPAN');
  });

  it('applies variant class', () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('nova-badge-success');
  });

  it('defaults to neutral variant', () => {
    const { container } = render(<Badge>Default</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('bg-gray-100');
  });

  it('applies size class', () => {
    const { container } = render(<Badge size="xs">Tiny</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('text-[10px]');
  });

  it('renders dot indicator when dot=true', () => {
    const { container } = render(<Badge dot variant="danger">Error</Badge>);
    // The dot is a nested span with rounded-full and a color class
    const dots = container.querySelectorAll('.rounded-full');
    // Both the outer badge and the inner dot have rounded-full
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  it('does not render dot by default', () => {
    const { container } = render(<Badge>NoDot</Badge>);
    // Only the badge itself has rounded-full
    const spans = container.querySelectorAll('span');
    expect(spans).toHaveLength(1);
  });

  it('passes additional HTML attributes', () => {
    render(<Badge data-testid="my-badge">Test</Badge>);
    expect(screen.getByTestId('my-badge')).toBeInTheDocument();
  });

  it('merges custom className', () => {
    const { container } = render(<Badge className="custom-class">Cls</Badge>);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('custom-class');
  });
});
