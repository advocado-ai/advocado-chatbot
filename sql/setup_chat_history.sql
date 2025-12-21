-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- Table for storing conversation threads
create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    title text not null default 'New Conversation',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Table for storing individual messages within a conversation
create table if not exists messages (
    id bigserial primary key,
    conversation_id uuid references conversations(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    sources jsonb, -- Stores the list of source objects (file_path, similarity, link, etc.)
    created_at timestamptz default now()
);

-- Index for faster retrieval of chat history
create index if not exists idx_messages_conversation_id on messages(conversation_id);
create index if not exists idx_conversations_updated_at on conversations(updated_at desc);
