/**
 * Tests for useLocalStorage hook.
 */

import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '@/hooks/useLocalStorage';

describe('useLocalStorage', () => {
  it('returns initial value when localStorage is empty', () => {
    const { result } = renderHook(() => useLocalStorage('key', 'default'));
    expect(result.current[0]).toBe('default');
  });

  it('reads existing value from localStorage', () => {
    localStorage.setItem('key', JSON.stringify('stored'));
    const { result } = renderHook(() => useLocalStorage('key', 'default'));
    expect(result.current[0]).toBe('stored');
  });

  it('writes value to localStorage on set', () => {
    const { result } = renderHook(() => useLocalStorage('key', 'init'));
    act(() => {
      result.current[1]('updated');
    });
    expect(result.current[0]).toBe('updated');
    expect(JSON.parse(localStorage.getItem('key')!)).toBe('updated');
  });

  it('supports updater function', () => {
    const { result } = renderHook(() => useLocalStorage('count', 0));
    act(() => {
      result.current[1]((prev) => prev + 1);
    });
    expect(result.current[0]).toBe(1);
  });

  it('handles complex objects', () => {
    const obj = { name: 'Nova', version: 1 };
    const { result } = renderHook(() => useLocalStorage('obj', obj));
    expect(result.current[0]).toEqual(obj);

    const updated = { name: 'Nova', version: 2 };
    act(() => {
      result.current[1](updated);
    });
    expect(result.current[0]).toEqual(updated);
    expect(JSON.parse(localStorage.getItem('obj')!)).toEqual(updated);
  });

  it('returns initial value on corrupted JSON', () => {
    localStorage.setItem('bad', '{broken');
    const { result } = renderHook(() => useLocalStorage('bad', 'fallback'));
    expect(result.current[0]).toBe('fallback');
  });
});
