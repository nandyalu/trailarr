---
description: 'Angular-specific coding standards and best practices'
applyTo: '**/*.ts, **/*.html, **/*.scss, **/*.css'
---

<!-- 
Copied from: https://github.com/github/awesome-copilot/blob/main/instructions/angular.instructions.md
And adapted from: https://angular.dev/ai/develop-with-ai
Adapted to fit the current project's needs.
-->

# Angular Development Instructions

Instructions for generating high-quality Angular applications with TypeScript, using Angular Signals for state management, adhering to Angular best practices as outlined at https://angular.dev.

## Project Context

- Latest Angular version (v20+, use standalone components by default)
- TypeScript for type safety
- Angular CLI for project setup and scaffolding
- Follow Angular Style Guide (https://angular.dev/style-guide)
- Use vanilla CSS or SCSS for styling (no CSS frameworks unless specified)

## Resources

Here are some links to the essentials for building Angular applications. Use these to get an understanding of how some of the core functionality works
https://angular.dev/essentials/components
https://angular.dev/essentials/signals
https://angular.dev/essentials/templates
https://angular.dev/essentials/dependency-injection

## Development Standards, Best Practices & Style Guide

### Coding Style guide

Here is a link to the most recent Angular style guide https://angular.dev/style-guide

### Architecture

- Use standalone components unless modules are explicitly required
- Organize code by standalone feature modules or domains for scalability
- Implement lazy loading for feature modules to optimize performance
- Use Angular's built-in dependency injection system effectively
- Structure components with a clear separation of concerns (smart vs. presentational components)

### TypeScript Best Practices

- Enable strict mode in `tsconfig.json` for type safety
- Define clear interfaces and types for components, services, and models
- Prefer type inference when the type is obvious
- Avoid the `any` type; use `unknown` when type is uncertain
- Use type guards and union types for robust type checking
- Implement proper error handling with RxJS operators (e.g., `catchError`)
- Use signal based forms for reactive forms

### Angular Best Practices

- Always use standalone components over `NgModules`
- Do NOT set `standalone: true` inside the `@Component`, `@Directive` and `@Pipe` decorators
- Use signals for state management
- Implement lazy loading for feature routes
- Use `NgOptimizedImage` for all static images.
- Do NOT use the `@HostBinding` and `@HostListener` decorators. Put host bindings inside the `host` object of the `@Component` or `@Directive` decorator instead

### Components

- Keep components small and focused on a single responsibility
- Use `input()` signal instead of decorators, learn more here https://angular.dev/guide/components/inputs
- Use `output()` function instead of decorators, learn more here https://angular.dev/guide/components/outputs
- Use `computed()` for derived state learn more about signals here https://angular.dev/guide/signals.
- Set `changeDetection: ChangeDetectionStrategy.OnPush` in `@Component` decorator for new components
- Do not use inline templates in any components
- Prefer signal forms instead of Template-driven ones or reactive forms
- Do NOT use `ngClass`, use `class` bindings instead, for context: https://angular.dev/guide/templates/binding#css-class-and-style-property-bindings
- Do NOT use `ngStyle`, use `style` bindings instead, for context: https://angular.dev/guide/templates/binding#css-class-and-style-property-bindings
- Follow Angular's component lifecycle hooks best practices
- Use ``viewChild()`, `viewChildren()`, `contentChild()` and `contentChildren()` functions instead of decorators
- Use Angular directives and pipes for reusable functionality

### State Management

- Use signals for local component state
- Use `signal()` for mutable state
- Use `computed()` for derived state
- Use `effect()` for side effects
- Keep state transformations pure and predictable
- Do NOT use `mutate` on signals, use `update` or `set` instead
- Handle loading and error states with signals and proper UI feedback
- Do not add API calls in components, use services for data fetching and management

### Templates

- Keep templates simple and avoid complex logic
- Use native control flow (`@if`, `@for`, `@switch`) instead of `*ngIf`, `*ngFor`, `*ngSwitch`
- Use signals from services for async data, and the async pipe to handle observables for other cases
- Use built in pipes and import pipes when being used in a template, learn more https://angular.dev/guide/templates/pipes#

### Styling

- Use Angular's component-level CSS encapsulation (default: ViewEncapsulation.Emulated)
- Prefer SCSS for styling with consistent theming (app theme variables are defined in `styles/styles.scss`, use them consistently that follow the design system)
- Implement responsive design using CSS Grid, Flexbox, and media queries
- Follow BEM (Block Element Modifier) naming conventions for CSS classes
- Maintain accessibility (a11y) with ARIA attributes and semantic HTML

### Services

- Place all service files in a dedicated `services` directory
- Place all API interaction logic within services
- Design high-level services that encapsulate business logic and data access around the single API endpoint (e.g., MediaService for media-related API calls and data handling used in media related components)
- Use the `providedIn: 'root'` option for singleton services
- Use the `inject()` function instead of constructor injection
- Use services to manage state with signals and share data between components
- Use `httpResource()` for RESTful API interactions where applicable, use Angular's `HttpClient` for other cases like POST requests, file uploads, etc., and handle responses with signals with proper typing
- Store API response data in signals for reactive updates

### Security

- Sanitize user inputs using Angular's built-in sanitization
- Implement route guards for authentication and authorization
- Use Angular's `HttpInterceptor` for CSRF protection and API authentication headers
- Validate form inputs with Angular's reactive forms and custom validators
- Follow Angular's security best practices (e.g., avoid direct DOM manipulation)

<!-- ### Testing
- Write unit tests for components, services, and pipes using Jest
- Use Angular's `TestBed` for component testing with mocked dependencies
- Test signal-based state updates using Angular's testing utilities
- Write end-to-end tests with Cypress or Playwright (if specified)
- Mock HTTP requests using `provideHttpClientTesting`
- Ensure high test coverage for critical functionality -->

## Implementation Process
1. Plan project structure and feature modules
2. Define TypeScript interfaces and models (in a `models` directory)
3. Scaffold components, services, and pipes using Angular CLI
4. Implement data services and API integrations with signal-based state
5. Build reusable components with clear inputs and outputs
6. Add reactive forms and validation
7. Apply styling with SCSS and responsive design
8. Implement lazy-loaded routes and guards
9. Add error handling and loading states using signals
10. Write unit and end-to-end tests
11. Optimize performance and bundle size

## Additional Guidelines
- Follow the Angular Style Guide for file naming conventions (see https://angular.dev/style-guide), e.g., use `feature.ts` for components and `feature-service.ts` for services. For legacy codebases, maintain consistency with existing pattern.
- Use Angular CLI commands for generating boilerplate code
- Document components and services with clear JSDoc comments
- Ensure accessibility compliance (WCAG 2.1) where applicable
- Use Angular's built-in i18n for internationalization (if specified)
- Keep code DRY by creating reusable utilities and shared modules
- Use signals consistently for state management to ensure reactive updates


## Examples

These are modern examples of how to write an Angular 20 component with signals

```ts
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';


@Component({
  selector: '{{tag-name}}-root',
  templateUrl: '{{tag-name}}.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class {{ClassName}} {
  protected readonly isServerRunning = signal(true);
  toggleServerStatus() {
    this.isServerRunning.update(isServerRunning => !isServerRunning);
  }
}
```

```css
.container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;

    button {
        margin-top: 10px;
    }
}
```

```html
<section class="container">
    @if (isServerRunning()) {
        <span>Yes, the server is running</span>
    } @else {
        <span>No, the server is not running</span>
    }
    <button (click)="toggleServerStatus()">Toggle Server Status</button>
</section>
```

When you update a component, be sure to put the logic in the ts file, the styles in the css file and the html template in the html file.

