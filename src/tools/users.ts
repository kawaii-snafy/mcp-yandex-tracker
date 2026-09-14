/** Users — https://yandex.ru/support/tracker/en/api/users/get-users.md */

import { z } from "zod";
import { given } from "../client.ts";
import { tool } from "../tool.ts";

export const userTools = [
  tool({
    name: "tracker_get_myself",
    description: `Get the Yandex Tracker user the token belongs to.

GET /v3/myself
https://yandex.ru/support/tracker/en/api/users/get-user-info.md`,
    input: {},
    run: (tracker) => tracker.request("GET", "/myself"),
  }),

  tool({
    name: "tracker_get_users",
    description: `Get the list of Yandex Tracker users in the organization.

GET /v3/users
https://yandex.ru/support/tracker/en/api/users/get-users.md

The endpoint page documents no filters — \`perPage\` and \`page\` are the
organization-wide pagination parameters from common-format.md. To search by
login, name or email, page through the list and filter the result yourself.`,
    input: {
      perPage: z
        .number()
        .int()
        .optional()
        .describe("Users per page. The result is paginated; default 50."),
      page: z.number().int().optional().describe("Page number. Default 1."),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/users", { params: given({ perPage: a.perPage, page: a.page }) }),
  }),

  tool({
    name: "tracker_get_user",
    description: `Get one Yandex Tracker user by login or uid.

GET /v3/users/{userId}
https://yandex.ru/support/tracker/en/api/users/get-user.md`,
    input: {
      userId: z
        .string()
        .min(1)
        .describe("User login or uid. A numeric login must be passed as login:12345."),
    },
    run: (tracker, a) => tracker.request("GET", `/users/${a.userId}`),
  }),

  tool({
    name: "tracker_get_users_relative",
    description: `List users with relative pagination, sorted by ascending uid.

GET /v3/users/_relative
https://yandex.ru/support/tracker/en/api/users/get-users-relative.md

Returns {users, hasNext}; pass the last uid as \`id\` to get the next page.
Unlike tracker_get_users this has no offset limit, so it is the one to use when
walking the whole organization.`,
    input: {
      perPage: z.number().int().optional().describe("Users per page, 1 to 100."),
      id: z.number().int().optional().describe("User uid to start the page from."),
      expand: z.string().optional().describe("Additional fields. `groups` adds group membership."),
    },
    run: (tracker, a) =>
      tracker.request("GET", "/users/_relative", {
        params: given({ perPage: a.perPage, id: a.id, expand: a.expand }),
      }),
  }),
];
