import {describe, expect, it} from 'vitest'
import {normalizeBaseUrl} from './api'

describe('API URL normalization', () => {
  it('removes all trailing slashes', () => expect(normalizeBaseUrl('https://api.example.test///')).toBe('https://api.example.test'))
  it('trims surrounding whitespace', () => expect(normalizeBaseUrl('  https://api.example.test  ')).toBe('https://api.example.test'))
})
