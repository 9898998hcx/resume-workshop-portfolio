import { describe, expect, it, vi } from 'vitest';
import { AiController } from './ai.controller.js';

describe('AI controller module actions', () => {
  it('forces the polish scenario and preserves the authenticated user id', async () => {
    const generate = vi.fn().mockResolvedValue({ generationId: 'g' });
    const controller = new AiController({ generate } as any);

    await controller.polish({ user: { id: 'owner' } } as any, {
      resumeId: 'resume',
      scenario: 'summary',
      sectionType: 'work',
      content: 'existing work content',
    });

    expect(generate).toHaveBeenCalledWith('owner', expect.objectContaining({
      resumeId: 'resume',
      scenario: 'polish',
    }));
    expect(generate.mock.calls[0][1].scenario).toBe('polish');
  });
});
