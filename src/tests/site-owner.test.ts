// @vitest-environment node
import { expect, it } from 'vitest'
import { siteOwner } from '../auth/site-owner'

const env = { SITE_IDENTITY_ALIASES: JSON.stringify({ 'owner@example.test': 'existing-site-owner' }) }
const req = (headers: Record<string, string>) => new Request('https://studio.test/', { headers })

it('recovers only a verified dispatcher email when the stable ID is absent', () => {
  expect(siteOwner(req({ 'oai-authenticated-user-email': 'Owner@example.test' }), env)).toBe('existing-site-owner')
  expect(siteOwner(req({ 'oai-authenticated-user-email': 'stranger@example.test' }), env)).toBeNull()
  expect(siteOwner(req({}), env)).toBeNull()
  expect(siteOwner(req({ 'x-user-email': 'owner@example.test' }), env)).toBeNull()
  expect(siteOwner(req({ 'oai-authenticated-user-full-name': 'owner@example.test' }), env)).toBeNull()
})

it('never overrides another authenticated user ID with an email alias', () => {
  expect(siteOwner(req({ 'oai-authenticated-user-id': 'another-owner', 'oai-authenticated-user-email': 'owner@example.test' }), env)).toBe('another-owner')
})

it.each([undefined, '', '{bad', 'null', '[]', '"string"', '{"owner@example.test":123}', '{"owner@example.test":""}', '{"owner@example.test":"../owner"}'])('fails closed for invalid mapping %s', value => {
  expect(siteOwner(req({ 'oai-authenticated-user-email': 'owner@example.test' }), { SITE_IDENTITY_ALIASES: value })).toBeNull()
})

it('does not resolve inherited object properties', () => {
  expect(siteOwner(req({ 'oai-authenticated-user-email': 'constructor' }), env)).toBeNull()
})
