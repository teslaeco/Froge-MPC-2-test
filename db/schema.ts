import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core'
export const products = sqliteTable('commerce_products', {
  id: text('id').primaryKey(), owner: text('owner').notNull(),
  payload: text('payload').notNull(), revision: integer('revision').notNull().default(1),
  updated: text('updated').notNull(),
}, table => [index('commerce_owner_updated').on(table.owner, table.updated)])
export const blenderConnections = sqliteTable('blender_connections', {
  owner: text('owner').primaryKey(), endpoint: text('endpoint').notNull(),
  credential: text('credential').notNull(), updated: text('updated').notNull(),
})
export const blenderJobs = sqliteTable('blender_jobs', {
  id: text('id').primaryKey(), owner: text('owner').notNull(), endpoint: text('endpoint').notNull(),
  prompt: text('prompt').notNull(), state: text('state').notNull(), detail: text('detail').notNull(),
  artifact: text('artifact'), created: text('created').notNull(), updated: text('updated').notNull(),
  referencePhotos: text('reference_photos').notNull().default('[]'),
}, table => [index('blender_jobs_owner_created').on(table.owner, table.created)])
