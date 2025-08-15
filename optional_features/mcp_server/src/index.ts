#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import * as fs from "fs/promises";
import * as path from "path";
import { fileURLToPath } from 'url';

// Define the root path of the trading system
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const TRADING_SYSTEM_ROOT = path.resolve(__dirname, "../../");

// Schema definitions
const ReadFileSchema = z.object({
  path: z.string().describe("Relative path from project root"),
});

const ListDirectorySchema = z.object({
  path: z.string().describe("Relative path from project root"),
});

const GetSystemStatusSchema = z.object({
  component: z.string().optional().describe("Specific component to check (optional)"),
});

const GetQuickReferenceSchema = z.object({
  category: z.enum(["commands", "architecture", "troubleshooting", "maintenance"])
    .describe("Category of quick reference to retrieve"),
});

// Trading System Documentation and Context
const SYSTEM_ARCHITECTURE = {
  core_components: {
    "app/main.py": "Main entry point with CLI commands (status, morning, evening, dashboard, news)",
    "app/core/sentiment/": "Two-stage sentiment analysis engine (Stage 1: lightweight, Stage 2: FinBERT)",
    "dashboard.py": "PRIMARY DASHBOARD - Streamlit-based trading sentiment analysis with ML performance metrics",
    "app/dashboard/": "Legacy web interface - superseded by root dashboard.py",
    "app/services/": "Business logic orchestration and daily management",
    "enhanced_ml_system/": "Enhanced ML pipeline with 54+ features and ensemble models",
    "frontend/": "React application with interactive charts (Port 3002)",
    "data/": "All application data including ML models, cache, and historical data"
  },
  
  dual_backend: {
    "port_8000": "Original API server (api_server.py)",
    "port_8001": "Enhanced ML API server (realtime_ml_api)",
    "description": "Dual backend architecture for backward compatibility and enhanced ML"
  },

  data_flow: {
    morning_routine: "Collect sentiment, news, technical indicators → Generate predictions",
    evening_routine: "Train ML models, validate predictions, export metrics",
    ml_pipeline: "75+ features → Ensemble models → Real-time predictions with caching"
  },

  project_organization: {
    core_files: "Essential system files kept in root (~25 files)",
    archive: "Legacy files and historical documentation moved to archive/ (~50 files)",
    helpers: "Utility scripts for monitoring, testing, and management moved to helpers/ (~40 files)",
    description: "Organized structure reduces root clutter while preserving functionality"
  },

  remote_deployment: {
    server: "170.64.199.151",
    location: "/root/test/",
    cron_jobs: "8 AM (premarket), 10 AM-4 PM (market hours), 6 PM (evening ML)",
    databases: "trading_analysis.db, morning_analysis.db"
  }
};

const QUICK_REFERENCES: Record<string, any> = {
  commands: {
    system_start: "pkill -f python && pkill -f node && ./start_complete_ml_system.sh",
    verification: "ps aux | grep -E '(api_server|realtime_ml_api|node.*serve)' | grep -v grep",
    daily_operations: {
      morning: "python -m app.main morning",
      evening: "python -m app.main evening", 
      dashboard: "source dashboard_venv/bin/activate && streamlit run dashboard.py  # PRIMARY DASHBOARD (uses dashboard_venv Python 3.12)",
      dashboard_legacy: "python -m app.main dashboard  # Legacy dashboard via app/",
      status: "python -m app.main status"
    },
    environments: {
      local_dashboard: "dashboard_venv (Python 3.12.7) - Use for dashboard.py locally",
      local_general: "venv (Python 3.13) - General development environment", 
      remote: "trading_venv - Use on remote server 170.64.199.151",
      activation: {
        dashboard_local: "source dashboard_venv/bin/activate",
        general_local: "source venv/bin/activate",
        remote: "source trading_venv/bin/activate  # On remote server"
      }
    },
    data_check: {
      training_data: "ssh root@170.64.199.151 'cd /root/test && python -c \"import sqlite3; conn = sqlite3.connect('data/ml_models/enhanced_training_data.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM enhanced_features'); print(f'Features: {cursor.fetchone()[0]}'); cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL'); print(f'Outcomes: {cursor.fetchone()[0]}')\"'",
      system_health: "curl -s http://localhost:8000/api/cache/status && curl -s http://localhost:8001/api/market-summary"
    },
    project_organization: {
      cleanup_legacy: "Move files according to PROJECT_ORGANIZATION_PLAN.md",
      archive_old: "mv legacy_files archive/",
      organize_helpers: "mv utility_scripts helpers/"
    }
  },

  architecture: {
    ml_stages: {
      stage1: "Continuous monitoring (~100MB) - TextBlob + VADER sentiment, 70% accuracy",
      stage2: "Enhanced analysis (~800MB) - FinBERT + RoBERTa + news classification, 85-95% accuracy"
    },
    performance_optimizations: "15-minute ML caching, request deduplication, 5x speed improvement",
    training_requirements: {
      minimum: "50+ features for basic training",
      recommended: "100+ features for reliable models", 
      optimal: "200+ features for high-quality predictions"
    },
    dashboards: {
      primary: "dashboard.py - Streamlit-based, latest implementation with ML performance metrics",
      legacy: "app/dashboard/enhanced_main.py - Superseded by root dashboard.py",
      frontend: "frontend/ - React application on Port 3002"
    }
  },

  troubleshooting: {
    port_conflicts: "lsof -ti:3000,3002,8000,8001 | xargs kill -9",
    memory_issues: "export SKIP_TRANSFORMERS=1 && python -m app.main morning",
    zombie_processes: "sudo pkill -9 python && sudo pkill -9 node",
    data_validation: "python export_and_validate_metrics.py"
  },

  validation_framework: {
    overview: "Comprehensive multi-layered validation system for dashboard, database, and ML data integrity",
    components: {
      dashboard_validation: {
        location: "helpers/export_and_validate_metrics.py",
        class: "MetricsValidator",
        purpose: "Validates dashboard metrics, sentiment data, ML performance, and database health",
        validates: [
          "ML performance metrics (success rates 0-100%, confidence 0-100%)",
          "Sentiment scores (-1 to +1 range, confidence 0-1 range)",
          "Feature analysis data (usage rates, record counts)",
          "Database statistics (table counts, recent activity)",
          "ASX bank data completeness (CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX, SUN.AX, QBE.AX)"
        ]
      },
      database_structure_validation: {
        location: "tests/test_data_validation.py",
        purpose: "Unit tests for database table data integrity",
        validates: [
          "Sentiment scores range [-1, 1]",
          "Confidence scores range [0, 1]", 
          "RSI values range [0, 100]",
          "Trading signal types (BUY, SELL, HOLD)",
          "ML prediction ranges and model version formats"
        ]
      },
      enhanced_ml_validation: {
        location: "app/core/ml/enhanced_training_pipeline.py",
        class: "DataValidator",
        purpose: "Validates ML features, training data, and prevents data leakage",
        validates: [
          "Sentiment data (ranges, required fields)",
          "Technical analysis data (RSI, price ranges)",
          "Training data (prevents future data leakage)",
          "Feature quality and ranges"
        ]
      },
      frontend_validation: {
        location: "frontend/src/components/IntegratedMLDashboard.tsx",
        purpose: "Frontend validation status display and integration",
        features: [
          "validation_status field in training status",
          "Visual indicators for validation results",
          "Color-coded validation status (green=passed, red=failed)"
        ]
      }
    },
    commands: {
      run_dashboard_validation: "python helpers/export_and_validate_metrics.py",
      run_database_tests: "python tests/test_data_validation.py",
      run_system_validation: "python helpers/validate_system.py",
      run_comprehensive_tests: "python run_comprehensive_tests.py",
      check_validation_results: "cat metrics_exports/validation_summary_$(date +%Y%m%d)*.txt"
    },
    generated_files: {
      location: "metrics_exports/",
      files: [
        "dashboard_metrics_{timestamp}.json - Raw exported data",
        "validation_results_{timestamp}.json - Detailed validation outcomes",
        "validation_summary_{timestamp}.txt - Human-readable summary"
      ],
      example_output: "Overall Status: PASS, Total Validations: 30, Passed: 30, Failed: 0, Warnings: 0"
    },
    quality_thresholds: {
      data_quality_score: "0.85 (Minimum 85% data quality)",
      average_confidence: "0.60 (Minimum 60% prediction confidence)",
      news_coverage: "0.70 (Minimum 70% news coverage)",
      sentiment_reliability: "0.75 (Minimum 75% sentiment reliability)"
    },
    validation_categories: {
      ml_performance: "Success rates (0-100%), confidence (0-100%), trade counts (non-negative)",
      sentiment_scores: "Sentiment values (-1 to +1), confidence (0-1), expected banks coverage",
      feature_analysis: "Feature usage rates (0-100%), record counts (positive), data completeness",
      database_statistics: "Table counts, recent activity (7 days), timestamp ranges"
    },
    automated_alerts: [
      "Data quality drops below 85%",
      "More than 2 banks fail validation",
      "Average confidence below 60%",
      "News coverage below 70%"
    ]
  },

  maintenance: {
    weekly: "python -m app.main status",
    monthly_cleanup: "find logs/ -name '*.log' -mtime +30 -delete",
    model_backup: "cp -r data/ml_models/ data/ml_models_backup_$(date +%Y%m%d)/",
    remote_monitoring: "./monitor_remote.sh",
    project_organization: "Follow PROJECT_ORGANIZATION_PLAN.md for file cleanup"
  }
};

const FILE_PURPOSES: Record<string, string> = {
  // Core Application
  "app/main.py": "CLI entry point with commands: status, morning, evening, dashboard, news",
  "app/core/sentiment/two_stage_analyzer.py": "Advanced sentiment engine with Stage 1 (lightweight) and Stage 2 (FinBERT)",
  "app/dashboard/enhanced_main.py": "Legacy dashboard - superseded by root dashboard.py",
  "dashboard.py": "PRIMARY DASHBOARD - Latest Streamlit-based trading sentiment analysis dashboard with ML performance metrics",
  "enhanced_ml_system/": "Complete ML pipeline with 54+ features, ensemble models, and caching",
  
  // API Servers
  "api_server.py": "Original API server (Port 8000) - backward compatibility",
  "integrated_ml_api_server.py": "Enhanced ML API server (Port 8001) - real-time ML predictions",
  
  // Frontend
  "frontend/": "React application with interactive charts, ML dashboards, technical analysis",
  
  // Data Management
  "data/ml_models/": "ML models, training data, performance metrics",
  "data/cache/": "API response caching, sentiment cache, news cache",
  "data/historical/": "Historical price data, sentiment history, trading signals",
  
  // Scripts & Automation
  "start_complete_ml_system.sh": "Complete system startup script",
  "deploy_memory_management.sh": "Memory optimization deployment",
  "monitor_remote.sh": "Remote system monitoring",
  "export_and_validate_metrics.py": "Primary validation framework - comprehensive dashboard metrics validation and export",
  
  // Validation Framework Files
  "helpers/export_and_validate_metrics.py": "MetricsValidator class - validates dashboard metrics, sentiment data, ML performance",
  "tests/test_data_validation.py": "Database structure validation tests - sentiment scores, confidence, RSI ranges",
  "helpers/validate_system.py": "Quick system validation summary - overall health check",
  "DATA_VALIDATION_SYSTEM.md": "Complete validation framework documentation with usage examples",
  "verify_dashboard.py": "Dashboard import and function validation tests",
  "verify_dashboard_data.py": "Dashboard data verification and source identification",
  "app/core/ml/enhanced_training_pipeline.py": "Contains DataValidator class for ML feature and training data validation",
  
  // System Organization
  "archive/": "Legacy files and historical documentation",
  "helpers/": "Utility scripts for monitoring, testing, and system management",
  
  // Documentation
  "GOLDEN_STANDARD_DOCUMENTATION.md": "Authoritative technical reference and operations guide",
  "README.md": "Project overview with architecture and commands",
  "ML_INTEGRATION_SUCCESS.md": "ML system implementation documentation",
  "MCP_SERVER_IMPLEMENTATION_COMPLETE.md": "Model Context Protocol server documentation",
  "PROJECT_ORGANIZATION_PLAN.md": "Project file organization and cleanup plan"
};

class TradingSystemMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "asx-trading-system-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "read_project_file",
            description: "Read any file from the trading system project",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Relative path from project root (e.g., 'app/main.py', 'GOLDEN_STANDARD_DOCUMENTATION.md')",
                },
              },
              required: ["path"],
            },
          },
          {
            name: "list_directory",
            description: "List contents of a directory in the project",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string", 
                  description: "Relative path from project root (e.g., 'app/', 'enhanced_ml_system/')",
                },
              },
              required: ["path"],
            },
          },
          {
            name: "get_system_status",
            description: "Get current status of the trading system components",
            inputSchema: {
              type: "object",
              properties: {
                component: {
                  type: "string",
                  description: "Specific component to check: 'api', 'ml', 'frontend', 'data', 'remote' (optional)",
                },
              },
            },
          },
          {
            name: "get_quick_reference",
            description: "Get quick reference guides for system operations",
            inputSchema: {
              type: "object",
              properties: {
                category: {
                  type: "string",
                  enum: ["commands", "architecture", "troubleshooting", "maintenance", "validation_framework"],
                  description: "Category of quick reference to retrieve",
                },
              },
              required: ["category"],
            },
          },
          {
            name: "get_validation_framework_info",
            description: "Get comprehensive information about the validation framework components and usage",
            inputSchema: {
              type: "object",
              properties: {
                component: {
                  type: "string",
                  enum: ["overview", "components", "commands", "files", "thresholds", "examples"],
                  description: "Specific validation framework component to get info about (optional)",
                },
              },
            },
          },
          {
            name: "explain_file_purpose",
            description: "Explain the purpose and role of any file in the trading system",
            inputSchema: {
              type: "object",
              properties: {
                filepath: {
                  type: "string",
                  description: "Path to the file to explain",
                },
              },
              required: ["filepath"],
            },
          },
          {
            name: "get_system_architecture",
            description: "Get comprehensive system architecture overview",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
        ],
      };
    });

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: "trading://system/architecture",
            mimeType: "application/json",
            name: "System Architecture",
            description: "Complete trading system architecture and component overview",
          },
          {
            uri: "trading://system/documentation", 
            mimeType: "text/markdown",
            name: "Golden Standard Documentation",
            description: "Authoritative technical reference and operations guide",
          },
          {
            uri: "trading://system/quick-reference",
            mimeType: "application/json", 
            name: "Quick Reference Commands",
            description: "Essential commands and operations for daily use",
          },
          {
            uri: "trading://system/validation-framework",
            mimeType: "application/json",
            name: "Validation Framework",
            description: "Comprehensive validation framework components, commands, and usage",
          },
        ],
      };
    });

    // Handle resource reading
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      switch (uri) {
        case "trading://system/architecture":
          return {
            contents: [
              {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(SYSTEM_ARCHITECTURE, null, 2),
              },
            ],
          };

        case "trading://system/documentation":
          try {
            const content = await fs.readFile(
              path.join(TRADING_SYSTEM_ROOT, "GOLDEN_STANDARD_DOCUMENTATION.md"),
              "utf-8"
            );
            return {
              contents: [
                {
                  uri,
                  mimeType: "text/markdown",
                  text: content,
                },
              ],
            };
          } catch (error) {
            throw new McpError(ErrorCode.InternalError, `Failed to read documentation: ${error}`);
          }

        case "trading://system/quick-reference":
          return {
            contents: [
              {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(QUICK_REFERENCES, null, 2),
              },
            ],
          };

        case "trading://system/validation-framework":
          return {
            contents: [
              {
                uri,
                mimeType: "application/json",
                text: JSON.stringify(QUICK_REFERENCES.validation_framework, null, 2),
              },
            ],
          };

        default:
          throw new McpError(ErrorCode.InvalidRequest, `Unknown resource: ${uri}`);
      }
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "read_project_file":
          return await this.readProjectFile(args);
        case "list_directory":
          return await this.listDirectory(args);
        case "get_system_status":
          return await this.getSystemStatus(args);
        case "get_quick_reference":
          return await this.getQuickReference(args);
        case "get_validation_framework_info":
          return await this.getValidationFrameworkInfo(args);
        case "explain_file_purpose":
          return await this.explainFilePurpose(args);
        case "get_system_architecture":
          return await this.getSystemArchitecture();
        default:
          throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
      }
    });
  }

  private async readProjectFile(args: any) {
    try {
      const { path: filePath } = ReadFileSchema.parse(args);
      const fullPath = path.join(TRADING_SYSTEM_ROOT, filePath);
      
      const content = await fs.readFile(fullPath, "utf-8");
      const stats = await fs.stat(fullPath);
      
      return {
        content: [
          {
            type: "text",
            text: `File: ${filePath}\nSize: ${stats.size} bytes\nLast Modified: ${stats.mtime.toISOString()}\n\n${content}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new McpError(ErrorCode.InvalidParams, `Invalid parameters: ${(error as any).message}`);
      }
      throw new McpError(ErrorCode.InternalError, `Failed to read file: ${error}`);
    }
  }

  private async listDirectory(args: any) {
    try {
      const { path: dirPath } = ListDirectorySchema.parse(args);
      const fullPath = path.join(TRADING_SYSTEM_ROOT, dirPath);
      
      const entries = await fs.readdir(fullPath, { withFileTypes: true });
      const listing = entries.map((entry: any) => ({
        name: entry.name,
        type: entry.isDirectory() ? "directory" : "file",
        purpose: FILE_PURPOSES[path.join(dirPath, entry.name)] || 
                 FILE_PURPOSES[entry.name] || 
                 "No specific purpose documented"
      }));

      return {
        content: [
          {
            type: "text",
            text: `Directory: ${dirPath}\n\n${JSON.stringify(listing, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new McpError(ErrorCode.InvalidParams, `Invalid parameters: ${(error as any).message}`);
      }
      throw new McpError(ErrorCode.InternalError, `Failed to list directory: ${error}`);
    }
  }

  private async getSystemStatus(args: any) {
    try {
      const { component } = GetSystemStatusSchema.parse(args);
      
      const status = {
        timestamp: new Date().toISOString(),
        system: "ASX Trading System with Enhanced ML",
        version: "v2.2 - Optimized Caching",
        
        components: {
          api_servers: {
            port_8000: "Original API (api_server.py)",
            port_8001: "Enhanced ML API (realtime_ml_api)",
            status: "Check with: curl http://localhost:8000/api/cache/status"
          },
          
          frontend: {
            port_3002: "React Dashboard with ML integration", 
            status: "Check with: curl http://localhost:3002"
          },
          
          ml_system: {
            stage1: "Lightweight sentiment (~100MB) - Always running",
            stage2: "Enhanced ML (~800MB) - On-demand with FinBERT",
            caching: "15-minute ML prediction caching for performance"
          },
          
          data: {
            training_requirements: "50+ features minimum, 100+ recommended",
            current_status: "Run data check command to see current counts",
            validation: "Auto-exports metrics during evening routine"
          },
          
          remote: {
            server: "170.64.199.151:/root/test/",
            cron_schedule: "8 AM, 10 AM-4 PM, 6 PM",
            monitoring: "./monitor_remote.sh"
          }
        },
        
        health_checks: {
          system_start: "pkill -f python && pkill -f node && ./start_complete_ml_system.sh",
          verify_running: "ps aux | grep -E '(api_server|realtime_ml_api|node.*serve)' | grep -v grep",
          test_endpoints: "curl -s http://localhost:8000/api/cache/status && curl -s http://localhost:8001/api/market-summary"
        }
      };

      if (component) {
        const componentStatus = status.components[component as keyof typeof status.components];
        if (!componentStatus) {
          throw new McpError(ErrorCode.InvalidParams, `Unknown component: ${component}`);
        }
        return {
          content: [
            {
              type: "text",
              text: `Component Status: ${component}\n\n${JSON.stringify(componentStatus, null, 2)}`,
            },
          ],
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `System Status\n\n${JSON.stringify(status, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new McpError(ErrorCode.InvalidParams, `Invalid parameters: ${(error as any).message}`);
      }
      throw new McpError(ErrorCode.InternalError, `Failed to get system status: ${error}`);
    }
  }

  private async getQuickReference(args: any) {
    try {
      const { category } = GetQuickReferenceSchema.parse(args);
      
      const reference = QUICK_REFERENCES[category];
      if (!reference) {
        throw new McpError(ErrorCode.InvalidParams, `Unknown category: ${category}`);
      }

      return {
        content: [
          {
            type: "text",
            text: `Quick Reference: ${category}\n\n${JSON.stringify(reference, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new McpError(ErrorCode.InvalidParams, `Invalid parameters: ${(error as any).message}`);
      }
      throw new McpError(ErrorCode.InternalError, `Failed to get quick reference: ${error}`);
    }
  }

  private async getValidationFrameworkInfo(args: any) {
    try {
      const { component } = args || {};
      
      const validationFramework = QUICK_REFERENCES.validation_framework;
      
      if (component) {
        const componentInfo = validationFramework[component as keyof typeof validationFramework];
        if (!componentInfo) {
          throw new McpError(ErrorCode.InvalidParams, `Unknown validation component: ${component}`);
        }
        return {
          content: [
            {
              type: "text",
              text: `Validation Framework - ${component}\n\n${JSON.stringify(componentInfo, null, 2)}`,
            },
          ],
        };
      }

      // Return complete validation framework info
      return {
        content: [
          {
            type: "text",
            text: `Comprehensive Validation Framework\n\n${JSON.stringify(validationFramework, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new McpError(ErrorCode.InvalidParams, `Invalid parameters: ${(error as any).message}`);
      }
      throw new McpError(ErrorCode.InternalError, `Failed to get validation framework info: ${error}`);
    }
  }

  private async explainFilePurpose(args: any) {
    try {
      const { filepath } = args;
      
      const purpose = FILE_PURPOSES[filepath] || 
                     FILE_PURPOSES[path.basename(filepath)] ||
                     "Purpose not documented - may be legacy or temporary file";

      const explanation = {
        file: filepath,
        purpose: purpose,
        category: this.categorizeFile(filepath),
        related_files: this.getRelatedFiles(filepath),
        usage_notes: this.getUsageNotes(filepath)
      };

      return {
        content: [
          {
            type: "text",
            text: `File Purpose Explanation\n\n${JSON.stringify(explanation, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new McpError(ErrorCode.InternalError, `Failed to explain file purpose: ${error}`);
    }
  }

  private async getSystemArchitecture() {
    return {
      content: [
        {
          type: "text",
          text: `ASX Trading System Architecture\n\n${JSON.stringify(SYSTEM_ARCHITECTURE, null, 2)}`,
        },
      ],
    };
  }

  private categorizeFile(filepath: string): string {
    if (filepath.startsWith("app/")) return "Core Application";
    if (filepath.startsWith("enhanced_ml_system/")) return "ML Pipeline";
    if (filepath.startsWith("frontend/")) return "React Frontend";
    if (filepath.startsWith("data/")) return "Data Storage";
    if (filepath.startsWith("logs/")) return "System Logs";
    if (filepath.startsWith("tests/")) return "Testing Framework";
    if (filepath.endsWith(".sh")) return "Shell Scripts";
    if (filepath.endsWith(".py") && filepath.includes("test")) return "Test Scripts";
    if (filepath.endsWith(".md")) return "Documentation";
    if (filepath.includes("api_server")) return "API Servers";
    return "Utility/Legacy";
  }

  private getRelatedFiles(filepath: string): string[] {
    const related: string[] = [];
    
    if (filepath.includes("morning")) {
      related.push("enhanced_morning_analyzer_with_ml.py", "app/main.py", "setup_morning_cron.sh");
    }
    if (filepath.includes("evening")) {
      related.push("enhanced_evening_analyzer_with_ml.py", "app/main.py", "run_safe_evening.sh");
    }
    if (filepath.includes("dashboard")) {
      related.push("app/dashboard/", "frontend/", "dashboard.py");
    }
    if (filepath.includes("ml") || filepath.includes("model")) {
      related.push("enhanced_ml_system/", "data/ml_models/", "export_and_validate_metrics.py");
    }
    if (filepath.includes("validation") || filepath.includes("validate")) {
      related.push("helpers/export_and_validate_metrics.py", "tests/test_data_validation.py", "helpers/validate_system.py", "DATA_VALIDATION_SYSTEM.md", "verify_dashboard.py", "verify_dashboard_data.py");
    }
    if (filepath.includes("export_and_validate_metrics")) {
      related.push("dashboard.py", "tests/test_data_validation.py", "metrics_exports/", "DATA_VALIDATION_SYSTEM.md");
    }
    if (filepath.includes("test_data_validation")) {
      related.push("helpers/export_and_validate_metrics.py", "app/core/ml/enhanced_training_pipeline.py", "DATA_VALIDATION_SYSTEM.md");
    }
    
    return related;
  }

  private getUsageNotes(filepath: string): string {
    if (filepath === "dashboard.py") {
      return "PRIMARY DASHBOARD - Latest Streamlit-based trading sentiment analysis dashboard. Use: streamlit run dashboard.py";
    }
    if (filepath === "app/dashboard/enhanced_main.py") {
      return "Legacy dashboard - superseded by root dashboard.py. Use dashboard.py instead.";
    }
    if (filepath === "app/main.py") {
      return "CLI entry point. Use 'python -m app.main <command>' where command is: status, morning, evening, dashboard, news";
    }
    if (filepath.includes("start_complete_ml_system.sh")) {
      return "Primary system startup script. Run after killing existing processes with: pkill -f python && pkill -f node";
    }
    if (filepath === "GOLDEN_STANDARD_DOCUMENTATION.md") {
      return "Authoritative reference. Contains all commands, troubleshooting, and system operations";
    }
    if (filepath.includes("api_server")) {
      return "Backend API servers. Port 8000 (original), Port 8001 (enhanced ML)";
    }
    if (filepath.includes("export_and_validate_metrics.py")) {
      return "Primary validation framework script. Run: python helpers/export_and_validate_metrics.py. Generates metrics_exports/ files.";
    }
    if (filepath.includes("test_data_validation.py")) {
      return "Database validation test suite. Run: python tests/test_data_validation.py. Tests sentiment scores, RSI ranges, etc.";
    }
    if (filepath.includes("validate_system.py")) {
      return "Quick system validation summary. Run: python helpers/validate_system.py. Provides overall health check.";
    }
    if (filepath === "DATA_VALIDATION_SYSTEM.md") {
      return "Complete validation framework documentation with usage examples and test descriptions";
    }
    if (filepath.includes("verify_dashboard")) {
      return "Dashboard verification scripts. Tests dashboard imports, data sources, and function integrity";
    }
    return "Refer to GOLDEN_STANDARD_DOCUMENTATION.md for detailed usage";
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("ASX Trading System MCP Server running on stdio");
  }
}

const server = new TradingSystemMCPServer();
server.run().catch(console.error);
