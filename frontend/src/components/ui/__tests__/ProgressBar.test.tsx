/**
 * Tests for ProgressBar component.
 */

import { render, screen } from '@testing-library/react';
import { ProgressBar } from '@/components/ui/ProgressBar';

describe('ProgressBar', () => {
  it('renders with role="progressbar"', () => {
    render(<ProgressBar value={50} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('sets aria-valuenow to the value', () => {
    render(<ProgressBar value={75} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '75');
  });

  it('sets aria-valuemin and aria-valuemax', () => {
    render(<ProgressBar value={50} max={200} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '200');
  });

  it('clamps percentage to 0-100', () => {
    const { container } = render(<ProgressBar value={-10} />);
    const inner = container.querySelector('[style]') as HTMLElement;
    expect(inner.style.width).toBe('0%');
  });

  it('clamps percentage at max', () => {
    const { container } = render(<ProgressBar value={150} />);
    const inner = container.querySelector('[style]') as HTMLElement;
    expect(inner.style.width).toBe('100%');
  });

  it('calculates percentage with custom max', () => {
    const { container } = render(<ProgressBar value={50} max={200} />);
    const inner = container.querySelector('[style]') as HTMLElement;
    expect(inner.style.width).toBe('25%');
  });

  it('renders label when provided', () => {
    render(<ProgressBar value={30} label="Reading Progress" />);
    expect(screen.getByText('Reading Progress')).toBeInTheDocument();
  });

  it('shows percentage value when showValue=true', () => {
    render(<ProgressBar value={45} showValue />);
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('hides label and value by default', () => {
    const { container } = render(<ProgressBar value={50} />);
    expect(container.querySelectorAll('.text-sm')).toHaveLength(0);
  });

  it('uses aria-label from label prop', () => {
    render(<ProgressBar value={50} label="Upload" />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-label', 'Upload');
  });

  it('uses default Progress aria-label when no label', () => {
    render(<ProgressBar value={50} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-label', 'Progress');
  });
});
