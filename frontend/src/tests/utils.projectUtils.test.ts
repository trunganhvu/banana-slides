import { describe, expect, test } from 'vitest';
import { parseMarkdownPages } from '@/utils/projectUtils';

describe('parseMarkdownPages', () => {
  test('imports sentence-style outline and required page text markers', () => {
    const pages = parseMarkdownPages(`
# Test verification logic

> : 



****
---  ---

# Test verification logic

- 

---  ---

Hình ảnh & Tư liệu
Bố cục & Trọng tâm
`);

    expect(pages).toHaveLength(1);
    expect(pages[0].title).toBe('');
    expect(pages[0].part).toBe('');
    expect(pages[0].points).toEqual(['']);
    expect(pages[0].text).toContain('---  ---');
    expect(pages[0].text).toContain('---  ---');
    expect(pages[0].extra_fields).toEqual({
      'Hình ảnh & Tư liệu': '',
      'Bố cục & Trọng tâm': '',
    });
  });

  test('imports outline content with or without markdown bullet prefixes', () => {
    const pages = parseMarkdownPages(`
# Test verification logic

****


* GPUAI
+ CUDA
- 

****
---  ---

---  ---
`);

    expect(pages[0].points).toEqual([
      '',
      'GPUAI',
      'CUDA',
      '',
    ]);
  });
});