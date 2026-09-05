import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core'
export const products = sqliteTable('commerce_products', {
  id: text('id').primaryKey(), owner: text('owner').notNull(),
  payload: text('payload').notNull(), revision: integer('revision').notNull().default(1),
  updated: text('updated').notNull(),
}, table => [index('commerce_owner_updated').on(table.owner, table.updated)])
