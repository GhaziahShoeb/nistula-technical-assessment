-- ============================================================
-- NISTULA UNIFIED MESSAGING PLATFORM
-- PostgreSQL Schema — Part 2 Assessment
-- ============================================================


-- ============================================================
-- TABLE 1: PROPERTIES
-- Stores each villa/apartment Nistula manages.
-- Kept separate so schema scales as Nistula adds properties.
-- ============================================================
CREATE TABLE properties (
    property_id         VARCHAR(50) PRIMARY KEY,        -- e.g. "villa-b1"
    property_name       VARCHAR(100) NOT NULL,          -- e.g. "Villa B1"
    location            VARCHAR(100),                   -- e.g. "Assagao, North Goa"
    bedrooms            SMALLINT,
    max_guests          SMALLINT,
    base_rate_inr       NUMERIC(10, 2),                 -- per night, up to base capacity
    extra_guest_rate    NUMERIC(10, 2),                 -- per night per extra guest
    checkin_time        TIME DEFAULT '14:00',
    checkout_time       TIME DEFAULT '11:00',
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- TABLE 2: GUESTS
-- One record per real human guest across ALL channels.
-- This is the hardest design problem — explained in README.
-- ============================================================
CREATE TABLE guests (
    guest_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name           VARCHAR(150),
    email               VARCHAR(150) UNIQUE,            -- best dedup key
    phone               VARCHAR(20) UNIQUE,             -- second best dedup key

    -- Channel-specific identifiers (nullable — guest may not use all channels)
    whatsapp_id         VARCHAR(100) UNIQUE,
    airbnb_guest_id     VARCHAR(100) UNIQUE,
    booking_com_id      VARCHAR(100) UNIQUE,
    instagram_handle    VARCHAR(100) UNIQUE,
    expedia_id          VARCHAR(100) UNIQUE,
    mmt_id              VARCHAR(100) UNIQUE,            -- MakeMyTrip
    agoda_id            VARCHAR(100) UNIQUE,

    -- Intelligence fields
    total_stays         SMALLINT DEFAULT 0,
    total_revenue_inr   NUMERIC(12, 2) DEFAULT 0,
    preferred_channel   VARCHAR(30),                    -- channel they use most
    tags                TEXT[],                         -- e.g. {"vip", "repeat", "corporate"}
    notes               TEXT,                           -- agent freeform notes

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast guest lookup by name (partial match searches)
CREATE INDEX idx_guests_name ON guests USING gin(to_tsvector('english', full_name));


-- ============================================================
-- TABLE 3: RESERVATIONS
-- One record per booking. Linked to guest and property.
-- A guest can have many reservations over time.
-- ============================================================
CREATE TABLE reservations (
    reservation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_ref         VARCHAR(50) UNIQUE NOT NULL,    -- e.g. "NIS-2024-0891"
    guest_id            UUID NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    property_id         VARCHAR(50) NOT NULL REFERENCES properties(property_id),

    -- Booking details
    source_channel      VARCHAR(30) NOT NULL,           -- where booking came from
    checkin_date        DATE NOT NULL,
    checkout_date       DATE NOT NULL,
    num_adults          SMALLINT NOT NULL DEFAULT 1,
    num_children        SMALLINT DEFAULT 0,
    total_amount_inr    NUMERIC(12, 2),
    amount_paid_inr     NUMERIC(12, 2) DEFAULT 0,

    -- Status lifecycle
    status              VARCHAR(30) NOT NULL DEFAULT 'enquiry'
                            CHECK (status IN (
                                'enquiry',      -- just asked, not confirmed
                                'confirmed',    -- booking confirmed
                                'checked_in',   -- guest is on property
                                'checked_out',  -- stay completed
                                'cancelled',    -- booking cancelled
                                'no_show'       -- guest didn't arrive
                            )),

    special_requests    TEXT,
    internal_notes      TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reservations_guest ON reservations(guest_id);
CREATE INDEX idx_reservations_dates ON reservations(checkin_date, checkout_date);
CREATE INDEX idx_reservations_status ON reservations(status);


-- ============================================================
-- TABLE 4: CONVERSATIONS
-- Groups related messages into one thread per guest per topic.
-- A guest could have multiple conversations:
--   e.g. one pre-booking, one during-stay, one post-stay.
-- ============================================================
CREATE TABLE conversations (
    conversation_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id            UUID NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    reservation_id      UUID REFERENCES reservations(reservation_id),   -- nullable: pre-booking has no reservation yet
    property_id         VARCHAR(50) REFERENCES properties(property_id),

    channel             VARCHAR(30) NOT NULL
                            CHECK (channel IN (
                                'whatsapp', 'booking_com', 'airbnb',
                                'instagram', 'expedia', 'mmt', 'agoda', 'direct'
                            )),

    status              VARCHAR(20) NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open', 'resolved', 'escalated')),

    opened_at           TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    resolved_by         VARCHAR(100)                    -- agent name or "auto"
);

CREATE INDEX idx_conversations_guest ON conversations(guest_id);
CREATE INDEX idx_conversations_status ON conversations(status);


-- ============================================================
-- TABLE 5: MESSAGES
-- Every single message across all channels in one table.
-- Core of the unified inbox. Tracks full AI lifecycle.
-- ============================================================
CREATE TABLE messages (
    message_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    guest_id            UUID NOT NULL REFERENCES guests(guest_id),

    -- Message content
    direction           VARCHAR(10) NOT NULL
                            CHECK (direction IN ('inbound', 'outbound')),
    message_text        TEXT NOT NULL,
    channel             VARCHAR(30) NOT NULL,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- AI processing fields (populated for inbound messages)
    query_type          VARCHAR(40)
                            CHECK (query_type IN (
                                'pre_sales_availability',
                                'pre_sales_pricing',
                                'post_sales_checkin',
                                'special_request',
                                'complaint',
                                'general_enquiry'
                            )),
    ai_confidence_score NUMERIC(4, 3)                  -- 0.000 to 1.000
                            CHECK (ai_confidence_score BETWEEN 0 AND 1),

    -- AI reply lifecycle (populated for outbound messages)
    ai_drafted_reply    TEXT,                           -- what Claude originally drafted
    reply_status        VARCHAR(20)
                            CHECK (reply_status IN (
                                'ai_drafted',           -- Claude wrote it, not sent yet
                                'agent_edited',         -- human modified before sending
                                'auto_sent',            -- sent automatically (score >= 0.85)
                                'agent_sent',           -- agent manually approved and sent
                                'escalated'             -- handed to human, no AI reply sent
                            )),
    agent_id            VARCHAR(100),                   -- which agent handled it (if any)
    sent_at             TIMESTAMPTZ,                    -- when outbound was actually sent

    -- Raw payload for debugging / audit
    raw_payload         JSONB,                          -- original webhook JSON stored as-is

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_guest ON messages(guest_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_query_type ON messages(query_type);
CREATE INDEX idx_messages_reply_status ON messages(reply_status);


-- ============================================================
-- TABLE 6: GUEST CHANNEL IDENTITIES
-- Alternative to storing all channel IDs on the guests table.
-- Used for future-proofing — adding a new channel means
-- inserting a row here, not altering the guests table.
-- (Bonus table — shows architectural thinking)
-- ============================================================
CREATE TABLE guest_channel_identities (
    identity_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id            UUID NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    channel             VARCHAR(30) NOT NULL,
    channel_guest_id    VARCHAR(150) NOT NULL,          -- the ID on that platform
    channel_username    VARCHAR(150),                   -- display name on that platform
    verified            BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (channel, channel_guest_id)                  -- same person can't register twice on one channel
);

CREATE INDEX idx_identities_guest ON guest_channel_identities(guest_id);
CREATE INDEX idx_identities_lookup ON guest_channel_identities(channel, channel_guest_id);