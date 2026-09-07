import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import "./Hint.css";

interface Props {
  /** The term itself, shown as the trigger and as the popup's heading. */
  term: string;
  /** Plain-language explanation. */
  text: string;
  className?: string;
}

/** Distance between the term and the popup. */
const GAP = 10;
/** Keep the popup this far from the edge of the viewport. */
const MARGIN = 8;

interface Position {
  top: number;
  left: number;
  /** Hidden until measured, so the first frame is not drawn in the wrong place. */
  ready: boolean;
}

/**
 * A term that explains itself: hover on a mouse, tap on a touchscreen.
 *
 * This replaces the `title` attribute, which looked like an answer but was not
 * one. A native tooltip cannot be opened by touch at all, so on a phone the
 * explanations were simply unreachable; it also takes about a second to appear,
 * cannot be styled, and truncates.
 *
 * The popup is rendered through a portal rather than next to the term. The
 * panels live inside `.app__main`, which scrolls, and a positioned element
 * inside a scrolling box is clipped at its edge -- so an in-place tooltip would
 * have been cut off exactly at the panel border where it needed to escape.
 *
 * Accessibility does not depend on the popup at all: the explanation sits in
 * the DOM permanently as a visually hidden element that the trigger points at
 * with `aria-describedby`, so a screen reader reads it whether or not anything
 * is open, and the popup itself is hidden from the accessibility tree to avoid
 * announcing the same sentence twice.
 */
export function Hint({ term, text, className }: Props) {
  const id = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<Position>({ top: 0, left: 0, ready: false });

  // How the last interaction arrived. A mouse gets hover, so its click must not
  // immediately undo what the hover just opened; touch and keyboard toggle.
  const pointerType = useRef("");

  const close = useCallback(() => {
    setOpen(false);
    setPosition((p) => ({ ...p, ready: false }));
  }, []);

  // Measured before paint: the popup's own size decides whether it fits below
  // the term or has to flip above it.
  useLayoutEffect(() => {
    if (!open) return;
    const trigger = triggerRef.current;
    const pop = popRef.current;
    if (!trigger || !pop) return;

    const anchor = trigger.getBoundingClientRect();
    const box = pop.getBoundingClientRect();

    const below = anchor.bottom + GAP;
    const above = anchor.top - box.height - GAP;
    // Prefer below; flip above only when below would run off the screen and
    // above actually has room, otherwise a flip just moves the problem.
    const top = below + box.height + MARGIN > window.innerHeight && above >= MARGIN
      ? above
      : below;

    const left = Math.min(
      Math.max(anchor.left, MARGIN),
      Math.max(MARGIN, window.innerWidth - box.width - MARGIN),
    );

    setPosition({ top, left, ready: true });
  }, [open, text]);

  useEffect(() => {
    if (!open) return;

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    // `pointerdown` rather than `click`: tapping a second term should close
    // this one before that one opens, and pointerdown lands first.
    const onOutside = (event: PointerEvent) => {
      if (!triggerRef.current?.contains(event.target as Node)) close();
    };
    // Closing rather than following the scroll. The popup is anchored to a
    // position on screen, and a panel that scrolls out from under it would
    // leave the explanation pointing at nothing.
    const onScroll = () => close();

    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onOutside);
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onOutside);
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [open, close]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className={`hint${className ? ` ${className}` : ""}`}
        aria-describedby={id}
        aria-expanded={open}
        onPointerDown={(event) => {
          pointerType.current = event.pointerType;
        }}
        onPointerEnter={(event) => {
          if (event.pointerType === "mouse") setOpen(true);
        }}
        onPointerLeave={(event) => {
          if (event.pointerType === "mouse") close();
        }}
        onClick={(event) => {
          // Keyboard activation reports no pointer detail, and focus has
          // already opened it; toggling here would close it again.
          if (event.detail === 0) return;
          // A mouse already opened this on hover; toggling would fight that.
          if (pointerType.current === "mouse") return;
          setOpen((was) => !was);
        }}
        onFocus={(event) => {
          // Only keyboard focus opens it. A press focuses the button too, and
          // on touch that raced the click: focus opened the popup and the
          // click that followed immediately toggled it shut, so a tap did
          // nothing at all. `:focus-visible` is exactly the distinction the
          // browser already draws between the two.
          if (event.target.matches(":focus-visible")) setOpen(true);
        }}
        onBlur={() => {
          pointerType.current = "";
          close();
        }}
      >
        {term}
      </button>

      {/* Always in the DOM, never drawn: this is what assistive technology
          reads, so the explanation does not depend on the popup being open. */}
      <span id={id} className="visually-hidden">
        {text}
      </span>

      {open &&
        createPortal(
          <div
            ref={popRef}
            className={`hint__pop${position.ready ? " hint__pop--placed" : ""}`}
            style={{ top: position.top, left: position.left }}
            aria-hidden="true"
          >
            <p className="hint__term">{term}</p>
            <p className="hint__text">{text}</p>
          </div>,
          document.body,
        )}
    </>
  );
}
