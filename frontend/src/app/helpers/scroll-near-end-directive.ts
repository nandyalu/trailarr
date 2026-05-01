import {
  AfterViewInit,
  DestroyRef,
  Directive,
  ElementRef,
  EventEmitter,
  inject,
  Input,
  Output,
} from '@angular/core';

@Directive({
  selector: '[appScrollNearEnd]',
  standalone: true,
})
export class ScrollNearEndDirective implements AfterViewInit {
  private readonly el = inject(ElementRef);
  private readonly destroyRef = inject(DestroyRef);

  @Output() nearEnd = new EventEmitter<void>();

  @Input() threshold = 200;

  private sentinel!: HTMLDivElement;
  private observer!: IntersectionObserver;

  ngAfterViewInit(): void {
    this.sentinel = document.createElement('div');
    this.sentinel.style.cssText = 'height:1px;width:1px;pointer-events:none;';
    this.el.nativeElement.appendChild(this.sentinel);

    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.nearEnd.emit();
            // Unobserve + re-observe after one rAF tick so the browser
            // re-evaluates intersection state — this re-fires on large screens
            // where the sentinel stays visible after new items are added,
            // driving the initial-load bootstrapping loop until content
            // overflows the viewport or the consumer's guard is hit.
            this.observer.unobserve(this.sentinel);
            requestAnimationFrame(() => {
              if (this.sentinel.isConnected) {
                this.observer.observe(this.sentinel);
              }
            });
          }
        }
      },
      { rootMargin: `0px 0px ${this.threshold}px 0px` },
    );

    this.observer.observe(this.sentinel);

    this.destroyRef.onDestroy(() => {
      this.observer.disconnect();
      this.sentinel.remove();
    });
  }
}
