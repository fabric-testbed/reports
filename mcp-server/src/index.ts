import express from "express";
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { AsyncLocalStorage } from "async_hooks";
// Import Express types correctly
import type { Request, Response } from "express";

// Enable debug logging to see what's happening
process.env.DEBUG = "mcp:*";

const app = express();
app.use(express.json());

// AsyncLocalStorage to carry per-request data (like incoming Authorization header)
const als = new AsyncLocalStorage<{ apiToken?: string }>();

const server = new McpServer({
  name: "Echo",
  version: "1.0.0"
});

// Register our capabilities
server.resource(
  "echo",
  new ResourceTemplate("echo://{message}", { list: undefined }),
  async (uri, { message }) => ({
    contents: [{
      uri: uri.href,
      text: `Resource echo: ${message}`
    }]
  })
);

server.tool(
  "echo",
  { message: z.string() },
  async ({ message }) => ({
    content: [{ type: "text", text: `Tool echo: ${message}` }]
  })
);

server.prompt(
  "echo",
  { message: z.string() },
  ({ message }) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Please process this message: ${message}`
      }
    }]
  })
);

app.post('/mcp', async (req: Request, res: Response) => {
  try {
    // Log incoming request for debugging
    console.log('Received request:', JSON.stringify(req.body, null, 2));

    // Extract incoming Authorization header (if any). Prefer exact 'authorization' header.
    const incomingAuth = (req.headers.authorization ?? req.headers.Authorization) as string | undefined;
    // Normalize to just the token string if it has Bearer prefix
    let incomingToken: string | undefined = undefined;
    if (incomingAuth) {
      const m = incomingAuth.match(/^Bearer\s+(.+)$/i);
      incomingToken = m ? m[1] : incomingAuth;
    }

    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    res.on('close', () => {
      console.log('Request closed');
      transport.close();
    });

    // Run server.connect and transport handling within ALS context so per-request
    // handlers can read the incoming token when making outbound API calls.
    await als.run({ apiToken: incomingToken }, async () => {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    });
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed. Use POST to interact with the MCP server. Follow README for details."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed. Use POST to interact with the MCP server. Follow README for details."
    },
    id: null
  }));
});

// Start the server
const PORT = process.env.MCP_SERVER_PORT || 4000;
app.listen(PORT, () => {
  console.log(`MCP Stateless Streamable HTTP Server listening on port ${PORT}`);
});
// Base URL for the API, can be overridden by the environment variable MCP_API_URL
const API_URL = process.env.MCP_API_URL || "https://reports.fabric-testbed.net/reports";
// Optional token for authenticated APIs (set MCP_API_TOKEN to a Bearer token)
const API_TOKEN = process.env.MCP_API_TOKEN || "";
console.log(`MCP API URL: ${API_URL}${API_TOKEN ? ' (auth token provided via MCP_API_TOKEN)' : ''}`);

// Helper function for making API requests
// Accepts an optional per-call token which, if provided, overrides the
// global MCP_API_TOKEN. This supports short-lived tokens passed by clients.
async function makeAPIRequest<T>(url: string, method: string = 'GET', body?: any, apiToken?: string): Promise<T | null> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  // Use per-call token if provided; otherwise fall back to the token from
  // AsyncLocalStorage (forwarded incoming Authorization header), then the
  // global MCP_API_TOKEN environment variable.
  const store = als.getStore?.();
  const tokenFromAls = store?.apiToken;
  const tokenToUse = apiToken || tokenFromAls || API_TOKEN;
  if (tokenToUse) {
    headers["Authorization"] = `Bearer ${tokenToUse}`;
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    console.error("Error making API request:", error);
    return null;
  }
}

// Interfaces for API responses
interface VersionData {
  reference: string;
  version: string;
}

interface UsersResponse {
  data: User[];
}

interface User {
  user_id: string;
  user_email: string;
  active: boolean;
  user_name: string;
  affiliation: string;
  registered_on: string;
  last_updated: string;
}

interface SitesResponse {
  data: Site[];
}

interface Site {
  name: string;
  hosts: Host[];
}

interface Host {
  name: string;
}

interface SlicesResponse {
  data: Slice[];
}

interface Slice {
  project_id: string;
  project_name: string;
  slice_id: string;
  slice_name: string;
  user_id: string;
  user_email: string;
  lease_start: string;
  lease_end: string;
  state: string;
  slivers: Sliver[];
}

interface SliversResponse {
  data: Sliver[];
}

interface Sliver {
  project_id: string;
  project_name: string;
  slice_id: string;
  slice_name: string;
  user_id: string;
  user_email: string;
  host: string;
  site: string;
  sliver_id: string;
  state: string;
}

interface ProjectsResponse {
  data: Project[];
}

interface Project {
  project_id: string;
  project_name: string;
  project_type: string;
  active: boolean;
  created_date: string;
  expires_on: string;
  retired_date: string;
  last_updated: string;
}

interface ProjectMembershipsResponse {
  data: ProjectMembership[];
}

interface ProjectMembership {
  project_id: string;
  project_name: string;
  project_type: string;
  active: boolean;
  created_date: string;
  expires_on: string;
  retired_date: string;
  last_updated: string;
}

// Register tools with MCP server

// @ts-ignore
server.tool(
  "get-version",
  "Get API version",
  { api_token: z.string().optional() },
  async ({ api_token }) => {
    const versionUrl = `${API_URL}/version`;
    const versionData = await makeAPIRequest<{ data: VersionData }>(versionUrl, 'GET', undefined, api_token);

    if (!versionData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve version data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `API Version: ${versionData.data.version}, Reference: ${versionData.data.reference}`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-users",
  "Get users",
  { api_token: z.string().optional() },
  async ({ api_token }) => {
    const usersUrl = `${API_URL}/users`;
    const usersData = await makeAPIRequest<UsersResponse>(usersUrl, 'GET', undefined, api_token);

    if (!usersData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve users data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${usersData.data.length} users.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-user-by-uuid",
  "Get specific user by UUID",
  {
    uuid: z.string().describe("User UUID"),
    api_token: z.string().optional(),
  },
  async ({ uuid, api_token }) => {
    const userUrl = `${API_URL}/users/${uuid}`;
    const userData = await makeAPIRequest<User>(userUrl, 'GET', undefined, api_token);

    if (!userData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve user data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `User: ${userData.user_name}, Email: ${userData.user_email}`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-user-memberships",
  "Get user memberships",
  {},
  async () => {
    const membershipsUrl = `${API_URL}/users/memberships`;
    const membershipsData = await makeAPIRequest<UsersResponse>(membershipsUrl);

    if (!membershipsData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve user memberships data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${membershipsData.data.length} user memberships.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-sites",
  "Get sites",
  {},
  async () => {
    const sitesUrl = `${API_URL}/sites`;
    const sitesData = await makeAPIRequest<SitesResponse>(sitesUrl);

    if (!sitesData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve sites data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${sitesData.data.length} sites.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-hosts",
  "Get hosts",
  {},
  async () => {
    const hostsUrl = `${API_URL}/hosts`;
    const hostsData = await makeAPIRequest<SitesResponse>(hostsUrl);

    if (!hostsData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve hosts data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${hostsData.data.length} hosts.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-slivers",
  "Get slivers",
  {},
  async () => {
    const sliversUrl = `${API_URL}/slivers`;
    const sliversData = await makeAPIRequest<SliversResponse>(sliversUrl);

    if (!sliversData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve slivers data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${sliversData.data.length} slivers.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "create-update-sliver",
  "Create/Update Sliver",
  {
    slice_id: z.string().describe("Slice ID"),
    sliver_id: z.string().describe("Sliver ID"),
    payload: z.object({
      // Define the structure of the payload based on the sliver schema
    }).describe("Sliver data"),
  },
  async ({ slice_id, sliver_id, payload }) => {
    const sliverUrl = `${API_URL}/slivers/${slice_id}/${sliver_id}`;
    const sliverData = await makeAPIRequest(sliverUrl, 'POST', payload);

    if (!sliverData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to create/update sliver",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: "Sliver created/updated successfully.",
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-projects",
  "Get projects",
  {},
  async () => {
    const projectsUrl = `${API_URL}/projects`;
    const projectsData = await makeAPIRequest<ProjectsResponse>(projectsUrl);

    if (!projectsData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve projects data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${projectsData.data.length} projects.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-project-by-uuid",
  "Get project by UUID",
  {
    uuid: z.string().describe("Project UUID"),
  },
  async ({ uuid }) => {
    const projectUrl = `${API_URL}/projects/${uuid}`;
    const projectData = await makeAPIRequest<Project>(projectUrl);

    if (!projectData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve project data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Project: ${projectData.project_name}, Type: ${projectData.project_type}`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-project-memberships",
  "Get project memberships",
  {},
  async () => {
    const membershipsUrl = `${API_URL}/projects/memberships`;
    const membershipsData = await makeAPIRequest<ProjectMembershipsResponse>(membershipsUrl);

    if (!membershipsData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve project memberships data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${membershipsData.data.length} project memberships.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "get-slices",
  "Get slices",
  {},
  async () => {
    const slicesUrl = `${API_URL}/slices`;
    const slicesData = await makeAPIRequest<SlicesResponse>(slicesUrl);

    if (!slicesData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to retrieve slices data",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Retrieved ${slicesData.data.length} slices.`,
        },
      ],
    };
  },
);

// @ts-ignore
server.tool(
  "create-update-slice",
  "Create/Update a slice",
  {
    slice_id: z.string().describe("Slice ID"),
    payload: z.object({
      // Define the structure of the payload based on the slice schema
    }).describe("Slice data"),
  },
  async ({ slice_id, payload }) => {
    const sliceUrl = `${API_URL}/slices/${slice_id}`;
    const sliceData = await makeAPIRequest(sliceUrl, 'POST', payload);

    if (!sliceData) {
      return {
        content: [
          {
            type: "text",
            text: "Failed to create/update slice",
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: "Slice created/updated successfully.",
        },
      ],
    };
  },
);
