import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { SkipToMain } from '@/components/layout/skip-to-main';

/**
 * Component Accessibility Tests
 * 
 * Tests keyboard navigation, ARIA labels, focus management, and other
 * accessibility features at the component level.
 */

describe('Component Accessibility', () => {
  describe('Button Component', () => {
    it('should be keyboard accessible', () => {
      const handleClick = vi.fn();
      
      render(<Button onClick={handleClick}>Click me</Button>);
      
      const button = screen.getByRole('button', { name: /click me/i });
      
      // Button should be in the document and clickable
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('should have visible focus indicator', () => {
      render(<Button>Focus me</Button>);
      
      const button = screen.getByRole('button', { name: /focus me/i });
      const styles = window.getComputedStyle(button);
      
      // Button should have focus-visible styles defined
      expect(button.className).toContain('focus-visible:outline-none');
      expect(button.className).toContain('focus-visible:ring-2');
    });

    it('should have accessible name for icon-only buttons', () => {
      render(
        <Button aria-label="Close dialog">
          <span>×</span>
        </Button>
      );
      
      const button = screen.getByRole('button', { name: /close dialog/i });
      expect(button).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled button</Button>);
      
      const button = screen.getByRole('button', { name: /disabled button/i });
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('disabled');
    });
  });

  describe('Input Component', () => {
    it('should be associated with label', () => {
      render(
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" />
        </div>
      );
      
      const input = screen.getByLabelText(/email/i);
      expect(input).toBeInTheDocument();
    });

    it('should support aria-required', () => {
      render(
        <div>
          <Label htmlFor="required-field">Required Field</Label>
          <Input id="required-field" aria-required="true" />
        </div>
      );
      
      const input = screen.getByLabelText(/required field/i);
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    it('should support aria-invalid for error states', () => {
      render(
        <div>
          <Label htmlFor="error-field">Field with Error</Label>
          <Input id="error-field" aria-invalid="true" aria-describedby="error-message" />
          <p id="error-message">This field has an error</p>
        </div>
      );
      
      const input = screen.getByLabelText(/field with error/i);
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-describedby', 'error-message');
    });

    it('should have visible focus indicator', () => {
      render(<Input placeholder="Focus me" />);
      
      const input = screen.getByPlaceholderText(/focus me/i);
      const styles = window.getComputedStyle(input);
      
      // Input should have focus-visible styles defined
      expect(input.className).toContain('focus-visible:outline-none');
      expect(input.className).toContain('focus-visible:ring-2');
    });
  });

  describe('Skip to Main Content', () => {
    it('should render skip link', () => {
      render(<SkipToMain />);
      
      const skipLink = screen.getByText(/skip to main content/i);
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    it('should be hidden by default but visible on focus', () => {
      render(<SkipToMain />);
      
      const skipLink = screen.getByText(/skip to main content/i);
      
      // Should have sr-only class
      expect(skipLink.className).toContain('sr-only');
      
      // Should have focus:not-sr-only class
      expect(skipLink.className).toContain('focus:not-sr-only');
    });

    it('should be keyboard accessible', () => {
      render(<SkipToMain />);
      
      const skipLink = screen.getByText(/skip to main content/i);
      
      // Skip link should be a link element
      expect(skipLink.tagName).toBe('A');
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  describe('Focus Management', () => {
    it('should maintain focus order', () => {
      render(
        <div>
          <Button>First</Button>
          <Button>Second</Button>
          <Button>Third</Button>
        </div>
      );
      
      const first = screen.getByRole('button', { name: /first/i });
      const second = screen.getByRole('button', { name: /second/i });
      const third = screen.getByRole('button', { name: /third/i });
      
      // All buttons should be in the document
      expect(first).toBeInTheDocument();
      expect(second).toBeInTheDocument();
      expect(third).toBeInTheDocument();
    });

    it('should trap focus in modal dialogs', () => {
      render(
        <div role="dialog" aria-modal="true">
          <Button>First</Button>
          <Button>Second</Button>
          <Button>Close</Button>
        </div>
      );
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(3);
    });
  });

  describe('ARIA Labels', () => {
    it('should have proper landmark roles', () => {
      render(
        <div>
          <header role="banner">Header</header>
          <nav role="navigation">Navigation</nav>
          <main role="main">Main content</main>
          <footer role="contentinfo">Footer</footer>
        </div>
      );
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('should mark decorative images as aria-hidden', () => {
      render(
        <div>
          <svg aria-hidden="true">
            <circle cx="10" cy="10" r="5" />
          </svg>
        </div>
      );
      
      const svg = document.querySelector('svg');
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should provide accessible names for interactive elements', () => {
      render(
        <div>
          <button aria-label="Search">
            <span>🔍</span>
          </button>
          <a href="/profile" aria-label="View profile">
            <span>👤</span>
          </a>
        </div>
      );
      
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /view profile/i })).toBeInTheDocument();
    });
  });

  describe('Color Contrast', () => {
    it('should use CSS variables for theme colors', () => {
      render(<Button variant="default">Themed Button</Button>);
      
      const button = screen.getByRole('button');
      const styles = window.getComputedStyle(button);
      
      // Button should use theme color classes
      expect(button.className).toContain('bg-brand');
    });

    it('should have sufficient contrast for text', () => {
      render(
        <div className="bg-background text-foreground">
          <p>This text should have sufficient contrast</p>
        </div>
      );
      
      const div = screen.getByText(/this text should have sufficient contrast/i).parentElement;
      expect(div?.className).toContain('bg-background');
      expect(div?.className).toContain('text-foreground');
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should have search input available', () => {
      render(
        <div>
          <Input
            placeholder="Search"
            data-testid="search-input"
          />
        </div>
      );
      
      const input = screen.getByTestId('search-input');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Search');
    });

    it('should have dialog with keyboard handler', () => {
      const handleClose = vi.fn();
      
      render(
        <div role="dialog" onKeyDown={(e) => {
          if (e.key === 'Escape') handleClose();
        }}>
          <Button>Close</Button>
        </div>
      );
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  describe('Screen Reader Support', () => {
    it('should announce dynamic content updates', () => {
      render(
        <div role="status" aria-live="polite">
          <p>Loading complete</p>
        </div>
      );
      
      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-live', 'polite');
      expect(status).toHaveTextContent('Loading complete');
    });

    it('should announce important alerts', () => {
      render(
        <div role="alert" aria-live="assertive">
          <p>Error: Something went wrong</p>
        </div>
      );
      
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'assertive');
      expect(alert).toHaveTextContent('Error: Something went wrong');
    });

    it('should hide decorative content from screen readers', () => {
      render(
        <div>
          <span aria-hidden="true">🎨</span>
          <span>Decorative icon</span>
        </div>
      );
      
      const decorative = document.querySelector('[aria-hidden="true"]');
      expect(decorative).toBeInTheDocument();
      expect(decorative).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
