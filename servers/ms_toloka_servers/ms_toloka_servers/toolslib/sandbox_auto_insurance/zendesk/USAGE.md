# Zendesk MCP Server Usage Guide

This document provides a comprehensive guide for using the Zendesk Mock Tools Server, including detailed information about available tools, query syntax, and OData filtering.

## Table of Contents

1. [Available Tools](#available-tools)
2. [Working with Tables](#working-with-tables)
3. [Search Articles Tool](#search-articles-tool)
4. [OData Filtering in get_items](#odata-filtering-in-get_items)
5. [CRUD Operations](#crud-operations)

---

## Available Tools

The Zendesk MCP server provides the following tools:

| Tool Name | Description |
|-----------|-------------|
| `get_tables` | Returns a list of all available Zendesk tables |
| `get_items` | Retrieves items from a specified table with optional filtering |
| `get_item` | Retrieves a single item by ID from a specified table |
| `create_item` | Creates a new item in a specified table |
| `update_item` | Updates an existing item in a specified table |
| `delete_item` | Deletes an item from a specified table |
| `search_articles` | Searches Zendesk help center articles with advanced query syntax |

---

## Working with Tables

### Available Tables

The Zendesk connector supports the following tables:

- **activities** - User and system activities
- **articles** - Help Center articles
- **groups** - Support groups
- **group_memberships** - Group membership records
- **organizations** - Customer organizations
- **requests** - Support requests
- **satisfaction_ratings** - Customer satisfaction ratings
- **sessions** - User sessions
- **tags** - Tags for categorization
- **targets** - Integration targets
- **tickets** - Support tickets
- **ticket_audits** - Ticket audit history
- **ticket_comments** - Comments on tickets (read-only for updates/deletes)
- **ticket_fields** - Custom ticket fields
- **ticket_metrics** - Ticket metrics and statistics
- **triggers** - Automation triggers
- **users** - User accounts
- **views** - Saved views

### Example: Getting Available Tables

```json
{
  "tool": "get_tables",
  "arguments": {}
}
```

Response:
```json
{
  "value": [
    { "Name": "activities", "DisplayName": "Activities" },
    { "Name": "articles", "DisplayName": "Articles" },
    { "Name": "tickets", "DisplayName": "Tickets" },
    ...
  ]
}
```

---

## Search Articles Tool

The `search_articles` tool provides powerful search capabilities for Zendesk Help Center articles, mimicking Zendesk's end-user search behavior.

### Basic Usage

```json
{
  "tool": "search_articles",
  "arguments": {
    "query": "password reset"
  }
}
```

### Query Syntax

The `query` parameter supports advanced search syntax with the following features:

#### 1. Simple Terms (AND Logic for ≤2 terms)

When searching with 1-2 words, **all terms must be present** in the article.

**Examples:**

```json
// Single word - finds articles containing "password"
{ "query": "password" }

// Two words - finds articles containing BOTH "password" AND "reset"
{ "query": "password reset" }
```

**Matching Rules:**
- For 1-2 terms: ALL terms must be present (AND logic)
- Case-insensitive matching
- Terms can appear anywhere in title or body

#### 2. Multiple Terms (40% Threshold)

When searching with **more than 2 terms**, at least **40% of terms** must match (rounded up).

**Examples:**

```json
// 6 terms - requires ceil(0.4 * 6) = 3 matches
{ "query": "network vpn configuration setup remote access" }

// 5 terms - requires ceil(0.4 * 5) = 2 matches
{ "query": "email smtp server settings configuration" }
```

**Calculation:**
- 3 terms → need 2 matches (40% of 3 = 1.2, rounded up to 2)
- 4 terms → need 2 matches (40% of 4 = 1.6, rounded up to 2)
- 5 terms → need 2 matches (40% of 5 = 2.0)
- 6 terms → need 3 matches (40% of 6 = 2.4, rounded up to 3)

#### 3. Exact Phrases (Double Quotes)

Use double quotes to search for **exact phrases** - words must appear together in the specified order.

**Examples:**

```json
// Exact phrase match
{ "query": "\"reset password\"" }

// Multiple phrases - ALL must be present
{ "query": "\"single sign on\" \"two factor\"" }

// Phrase + term
{ "query": "\"password reset\" authentication" }
```

**Rules:**
- All phrases in quotes are **mandatory**
- Words must appear **consecutively** and in **exact order**
- Case-insensitive

#### 4. Negative Terms and Phrases

Exclude articles containing specific terms or phrases using the minus sign (`-`).

**Examples:**

```json
// Exclude single word
{ "query": "printer -installation" }
// Finds articles with "printer" but WITHOUT "installation"

// Exclude phrase
{ "query": "password -\"admin panel\"" }
// Finds articles with "password" but WITHOUT the phrase "admin panel"

// Combined negative terms
{ "query": "email -deprecated -obsolete" }
// Finds articles with "email" but WITHOUT "deprecated" or "obsolete"
```

**Rules:**
- If any negative term/phrase is found, article is **excluded**
- Can combine with positive terms and phrases
- Case-insensitive

#### 5. Single Quotes (Ignored)

Single quotes are **ignored** in search queries.

**Example:**

```json
// These are equivalent:
{ "query": "'word' test" }
{ "query": "word test" }
```

### Advanced Query Examples

#### Example 1: Troubleshooting Search
```json
{
  "query": "\"network connectivity\" vpn -wifi"
}
```
**Logic:**
- Must contain phrase: "network connectivity"
- Must contain term: "vpn"
- Must NOT contain: "wifi"

#### Example 2: Complex Multi-Term Search
```json
{
  "query": "authentication security login password token session"
}
```
**Logic:**
- 6 terms total → requires 3 matches (40%)
- Article needs at least 3 of these words

#### Example 3: Multiple Phrases with Exclusion
```json
{
  "query": "\"two factor\" \"authentication\" -\"deprecated\" -legacy"
}
```
**Logic:**
- Must contain both phrases: "two factor" AND "authentication"
- Must NOT contain: "deprecated" or "legacy"

### Additional Filtering Parameters

Beyond the `query` parameter, you can filter results using:

#### Filter by Locale
```json
{
  "query": "password",
  "locale": "en-us"
}
```

#### Filter by Brand
```json
{
  "query": "setup",
  "brand_id": 1001
}
```

#### Enable Multi-Brand Search
```json
{
  "query": "guide",
  "brand_id": 1001,
  "multibrand": true
}
```
**Note:** When `multibrand` is `true`, the `brand_id` filter is ignored.

#### Filter by Category
```json
{
  "query": "installation",
  "category": 11
}
```

#### Filter by Section
```json
{
  "query": "troubleshoot",
  "section": 100
}
```

#### Filter by Labels
```json
{
  "query": "error",
  "label_names": "printer,hardware"
}
```

### Combined Example

```json
{
  "query": "\"password reset\" authentication -deprecated",
  "locale": "en-us",
  "brand_id": 1001,
  "category": 12,
  "label_names": "security,account"
}
```

This searches for:
- Articles containing the phrase "password reset"
- Articles containing the term "authentication"
- Articles NOT containing "deprecated"
- In English (US) locale
- For brand 1001
- In category 12
- Tagged with "security" OR "account"

---

## OData Filtering in get_items

The `get_items` tool supports **OData v4** filtering protocol for advanced queries.

### Basic Usage

```json
{
  "tool": "get_items",
  "arguments": {
    "table": "tickets",
    "filter": "status eq 'open'"
  }
}
```

### Supported OData Operators

#### 1. Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal to | `status eq 'open'` |
| `ne` | Not equal to | `status ne 'closed'` |
| `gt` | Greater than | `priority gt 2` |
| `ge` | Greater than or equal | `priority ge 3` |
| `lt` | Less than | `vote_count lt 10` |
| `le` | Less than or equal | `vote_count le 5` |

#### 2. Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Logical AND | `status eq 'open' and priority eq 'high'` |
| `or` | Logical OR | `status eq 'open' or status eq 'new'` |

### Field Types and Values

#### String Fields
Use single quotes around string values:
```
status eq 'open'
type eq 'incident'
locale eq 'en-us'
```

#### Integer Fields
No quotes needed:
```
priority eq 3
id eq 12345
section_id eq 100
```

#### Boolean Fields
Use lowercase `true` or `false`:
```
draft eq false
promoted eq true
comments_disabled eq false
```

#### Enum Fields
Treat as strings with single quotes:
```
status eq 'open'
priority eq 'high'
type eq 'problem'
```

### OData Filter Examples

#### Example 1: Filter Tickets by Status
```json
{
  "table": "tickets",
  "filter": "status eq 'open'"
}
```

#### Example 2: Filter by Multiple Conditions (AND)
```json
{
  "table": "tickets",
  "filter": "status eq 'open' and priority eq 'high'"
}
```

#### Example 3: Filter by Multiple Conditions (OR)
```json
{
  "table": "tickets",
  "filter": "status eq 'open' or status eq 'new'"
}
```

#### Example 4: Numeric Comparisons
```json
{
  "table": "articles",
  "filter": "vote_count gt 10"
}
```

#### Example 5: Complex Conditions
```json
{
  "table": "tickets",
  "filter": "(status eq 'open' or status eq 'new') and priority eq 'high'"
}
```

#### Example 6: Filter Comments by Ticket ID
```json
{
  "table": "ticket_comments",
  "filter": "ticket_id eq 23"
}
```

#### Example 7: Filter by Boolean
```json
{
  "table": "articles",
  "filter": "draft eq false and promoted eq true"
}
```

### Additional get_items Parameters

#### Select Specific Fields
```json
{
  "table": "tickets",
  "select": "id,status,subject,priority"
}
```

#### Order Results
```json
{
  "table": "tickets",
  "orderby": "created_at desc"
}
```

#### Limit Results
```json
{
  "table": "tickets",
  "top": 10
}
```

#### Skip Results (Pagination)
```json
{
  "table": "tickets",
  "skip": 20,
  "top": 10
}
```

### Combined Example

```json
{
  "table": "tickets",
  "filter": "status eq 'open' and priority gt 2",
  "select": "id,subject,status,priority",
  "orderby": "created_at desc",
  "top": 50
}
```

This query:
- Filters tickets where status is 'open' AND priority > 2
- Returns only specified fields
- Orders by creation date (newest first)
- Limits to 50 results

---

## CRUD Operations

### Create Item

Create new records in Zendesk tables.

**Example: Create a Ticket**
```json
{
  "tool": "create_item",
  "arguments": {
    "table": "tickets",
    "item": {
      "subject": "Printer not working",
      "description": "Office printer is offline",
      "status": "open",
      "priority": "high",
      "requester_id": 12345,
      "assignee_id": 67890
    }
  }
}
```

**Example: Create a Ticket Comment**
```json
{
  "tool": "create_item",
  "arguments": {
    "table": "ticket_comments",
    "item": {
      "ticket_id": 23,
      "author_id": 22677105199388,
      "body": "Investigating the issue",
      "public": true
    }
  }
}
```

**Note:**
- `ticket_comments` auto-generates `html_body` from `body`
- IDs are auto-generated if not provided

### Get Item

Retrieve a single item by ID.

**Example:**
```json
{
  "tool": "get_item",
  "arguments": {
    "table": "tickets",
    "id": "1"
  }
}
```

### Update Item

Update an existing record.

**Example:**
```json
{
  "tool": "update_item",
  "arguments": {
    "table": "tickets",
    "id": "1",
    "item": {
      "status": "pending",
      "priority": "high"
    }
  }
}
```

**Restrictions:**
- **Cannot update `ticket_comments`** - Comments are read-only after creation

### Delete Item

Delete a record from a table.

**Example:**
```json
{
  "tool": "delete_item",
  "arguments": {
    "table": "tickets",
    "id": "1"
  }
}
```

**Restrictions:**
- **Cannot delete `ticket_comments`** - Comments are permanent once created

---

## Error Handling

### Common Errors

#### Item Not Found
```json
{
  "error": "Item with id '999' not found in table 'tickets'"
}
```

#### Invalid Table
```json
{
  "error": "Input validation failed: table: Input should be 'tickets', 'users', 'organizations', 'comments' or 'ticket_comments'"
}
```

#### Update/Delete Restriction
```json
{
  "error": "The value is not updatable. Ticket comments cannot be modified."
}
```

---

## Best Practices

### 1. Search Articles Efficiently

- Use exact phrases for specific concepts: `"two factor authentication"`
- Use negative terms to exclude irrelevant results: `-deprecated`
- Combine filters for precise results: add `category`, `section`, or `brand_id`

### 2. OData Filtering

- Always use single quotes for string values
- Parentheses help with complex logic: `(A or B) and C`
- Test simple filters first, then add complexity

### 3. Pagination

For large result sets, use `top` and `skip`:
```json
// First page
{ "table": "tickets", "top": 50, "skip": 0 }

// Second page
{ "table": "tickets", "top": 50, "skip": 50 }
```

### 4. Field Selection

Only request fields you need for better performance:
```json
{
  "table": "tickets",
  "select": "id,subject,status"
}
```

---

## Additional Resources

- **OData v4 Specification**: https://www.odata.org/documentation/
- **Zendesk API Documentation**: https://developer.zendesk.com/api-reference/

---

## Support

For issues or questions about the Zendesk MCP server, please refer to the main repository documentation or contact your system administrator.
