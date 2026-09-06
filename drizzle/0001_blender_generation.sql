CREATE TABLE `blender_connections` (
	`owner` text PRIMARY KEY NOT NULL,
	`endpoint` text NOT NULL,
	`credential` text NOT NULL,
	`updated` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `blender_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`endpoint` text NOT NULL,
	`prompt` text NOT NULL,
	`state` text NOT NULL,
	`detail` text NOT NULL,
	`artifact` text,
	`created` text NOT NULL,
	`updated` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `blender_jobs_owner_created` ON `blender_jobs` (`owner`,`created`);