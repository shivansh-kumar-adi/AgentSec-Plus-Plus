import {describe, expect, it} from 'vitest'
import {routeDefinitions} from './routeConfig'

describe('SOC route map', () => {
  it('defines 13 unique, direct-access routes', () => {
    expect(routeDefinitions).toHaveLength(13)
    expect(new Set(routeDefinitions.map(route => route.path)).size).toBe(13)
    routeDefinitions.forEach(route => expect(route.path).toMatch(/^\/[a-z-]+$/))
  })

  it('provides a distinct navigation label for every route', () => {
    expect(new Set(routeDefinitions.map(route => route.label)).size).toBe(13)
  })
})
