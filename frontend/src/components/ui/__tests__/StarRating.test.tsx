/**
 * Tests for StarRating component.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { StarRating } from '@/components/ui/StarRating';

// Mock Heroicons to avoid SVG import issues in jsdom
vi.mock('@heroicons/react/24/solid', () => ({
  StarIcon: (props: Record<string, unknown>) => <svg data-testid="star-filled" {...props} />,
}));
vi.mock('@heroicons/react/24/outline', () => ({
  StarIcon: (props: Record<string, unknown>) => <svg data-testid="star-outline" {...props} />,
}));

describe('StarRating', () => {
  it('renders correct number of stars', () => {
    render(<StarRating value={3} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(5); // default max=5
  });

  it('renders custom number of stars', () => {
    render(<StarRating value={2} max={10} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(10);
  });

  it('shows correct filled/outline stars for value=3', () => {
    render(<StarRating value={3} />);
    const filled = screen.getAllByTestId('star-filled');
    const outline = screen.getAllByTestId('star-outline');
    expect(filled).toHaveLength(3);
    expect(outline).toHaveLength(2);
  });

  it('buttons are disabled in readonly mode', () => {
    render(<StarRating value={4} readonly />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it('calls onChange with clicked star value', () => {
    const onChange = vi.fn();
    render(<StarRating value={2} onChange={onChange} />);
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[3]!); // 4th star = value 4
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it('does not call onChange in readonly mode', () => {
    const onChange = vi.fn();
    render(<StarRating value={2} onChange={onChange} readonly />);
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]!);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('renders label when showLabel is true', () => {
    render(<StarRating value={3.5} showLabel />);
    expect(screen.getByText('3.5')).toBeInTheDocument();
  });

  it('does not render label by default', () => {
    render(<StarRating value={3} />);
    expect(screen.queryByText('3.0')).not.toBeInTheDocument();
  });

  it('each star has aria-label', () => {
    render(<StarRating value={1} />);
    expect(screen.getByLabelText('1 star')).toBeInTheDocument();
    expect(screen.getByLabelText('2 stars')).toBeInTheDocument();
  });

  it('value=0 shows all outline stars', () => {
    render(<StarRating value={0} />);
    const outline = screen.getAllByTestId('star-outline');
    expect(outline).toHaveLength(5);
    expect(screen.queryAllByTestId('star-filled')).toHaveLength(0);
  });
});
