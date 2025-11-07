/**
 * Database connection utilities and query builders
 * Supports BigQuery and Cloud SQL (PostgreSQL)
 */

import { BigQuery } from '@google-cloud/bigquery';
import { Pool, PoolConfig } from 'pg';

/**
 * BigQuery client singleton
 */
let bigQueryClient: BigQuery | null = null;

export function getBigQueryClient(): BigQuery {
  if (!bigQueryClient) {
    bigQueryClient = new BigQuery({
      projectId: process.env.GCP_PROJECT_ID,
      keyFilename: process.env.GCP_KEY_FILE,
    });
  }
  return bigQueryClient;
}

/**
 * Cloud SQL (PostgreSQL) connection pool
 */
let pgPool: Pool | null = null;

export function getPostgresPool(): Pool {
  if (!pgPool) {
    const config: PoolConfig = {
      host: process.env.POSTGRES_HOST,
      port: parseInt(process.env.POSTGRES_PORT || '5432'),
      database: process.env.POSTGRES_DB,
      user: process.env.POSTGRES_USER,
      password: process.env.POSTGRES_PASSWORD,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    };
    pgPool = new Pool(config);
  }
  return pgPool;
}

/**
 * BigQuery query builder for insights
 */
export class BigQueryInsightBuilder {
  private dataset: string;
  private table: string;
  private filters: string[] = [];
  private orderBy: string = 'created_at DESC';
  private limitValue: number = 20;
  private offsetValue: number = 0;

  constructor(dataset: string = 'intel', table: string = 'insights') {
    this.dataset = dataset;
    this.table = table;
  }

  whereSignalType(signalType: string): this {
    this.filters.push(`signal_type = '${signalType}'`);
    return this;
  }

  whereConfidenceGreaterThan(confidence: number): this {
    this.filters.push(`confidence >= ${confidence}`);
    return this;
  }

  whereBlockHeightGreaterThan(blockHeight: number): this {
    this.filters.push(`block_height > ${blockHeight}`);
    return this;
  }

  whereTimestampAfter(timestamp: Date): this {
    this.filters.push(`created_at > TIMESTAMP('${timestamp.toISOString()}')`);
    return this;
  }

  orderByCreatedAt(direction: 'ASC' | 'DESC' = 'DESC'): this {
    this.orderBy = `created_at ${direction}`;
    return this;
  }

  limit(limit: number): this {
    this.limitValue = limit;
    return this;
  }

  offset(offset: number): this {
    this.offsetValue = offset;
    return this;
  }

  build(): string {
    let query = `SELECT * FROM \`${this.dataset}.${this.table}\``;
    
    if (this.filters.length > 0) {
      query += ` WHERE ${this.filters.join(' AND ')}`;
    }
    
    query += ` ORDER BY ${this.orderBy}`;
    query += ` LIMIT ${this.limitValue}`;
    
    if (this.offsetValue > 0) {
      query += ` OFFSET ${this.offsetValue}`;
    }
    
    return query;
  }

  async execute(): Promise<any[]> {
    const client = getBigQueryClient();
    const query = this.build();
    const [rows] = await client.query({ query });
    return rows;
  }
}

/**
 * BigQuery query builder for signals
 */
export class BigQuerySignalBuilder {
  private dataset: string;
  private table: string;
  private filters: string[] = [];
  private orderBy: string = 'processed_at DESC';
  private limitValue: number = 100;

  constructor(dataset: string = 'intel', table: string = 'signals') {
    this.dataset = dataset;
    this.table = table;
  }

  whereType(type: string): this {
    this.filters.push(`type = '${type}'`);
    return this;
  }

  whereBlockHeight(blockHeight: number): this {
    this.filters.push(`block_height = ${blockHeight}`);
    return this;
  }

  whereStrengthGreaterThan(strength: number): this {
    this.filters.push(`strength >= ${strength}`);
    return this;
  }

  whereTimestampAfter(timestamp: Date): this {
    this.filters.push(`processed_at > TIMESTAMP('${timestamp.toISOString()}')`);
    return this;
  }

  limit(limit: number): this {
    this.limitValue = limit;
    return this;
  }

  build(): string {
    let query = `SELECT * FROM \`${this.dataset}.${this.table}\``;
    
    if (this.filters.length > 0) {
      query += ` WHERE ${this.filters.join(' AND ')}`;
    }
    
    query += ` ORDER BY ${this.orderBy}`;
    query += ` LIMIT ${this.limitValue}`;
    
    return query;
  }

  async execute(): Promise<any[]> {
    const client = getBigQueryClient();
    const query = this.build();
    const [rows] = await client.query({ query });
    return rows;
  }
}

/**
 * PostgreSQL query builder for user alerts
 */
export class PostgresAlertBuilder {
  private table: string = 'user_alerts';
  private filters: string[] = [];
  private params: any[] = [];
  private paramCounter: number = 1;

  whereUserId(userId: string): this {
    this.filters.push(`user_id = $${this.paramCounter}`);
    this.params.push(userId);
    this.paramCounter++;
    return this;
  }

  whereIsActive(isActive: boolean): this {
    this.filters.push(`is_active = $${this.paramCounter}`);
    this.params.push(isActive);
    this.paramCounter++;
    return this;
  }

  whereSignalType(signalType: string): this {
    this.filters.push(`signal_type = $${this.paramCounter}`);
    this.params.push(signalType);
    this.paramCounter++;
    return this;
  }

  build(): { query: string; params: any[] } {
    let query = `SELECT * FROM ${this.table}`;
    
    if (this.filters.length > 0) {
      query += ` WHERE ${this.filters.join(' AND ')}`;
    }
    
    query += ` ORDER BY created_at DESC`;
    
    return { query, params: this.params };
  }

  async execute(): Promise<any[]> {
    const pool = getPostgresPool();
    const { query, params } = this.build();
    const result = await pool.query(query, params);
    return result.rows;
  }
}

/**
 * Helper function to insert insight into BigQuery
 */
export async function insertInsight(insight: any): Promise<void> {
  const client = getBigQueryClient();
  await client
    .dataset('intel')
    .table('insights')
    .insert([insight]);
}

/**
 * Helper function to insert signal into BigQuery
 */
export async function insertSignal(signal: any): Promise<void> {
  const client = getBigQueryClient();
  await client
    .dataset('intel')
    .table('signals')
    .insert([signal]);
}

/**
 * Helper function to close database connections
 */
export async function closeDatabaseConnections(): Promise<void> {
  if (pgPool) {
    await pgPool.end();
    pgPool = null;
  }
}
