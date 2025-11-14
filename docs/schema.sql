CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  nickname VARCHAR(64) NOT NULL,
  wechat_openid VARCHAR(64),
  email VARCHAR(128),
  password_hash VARCHAR(128),
  lang VARCHAR(8),
  status VARCHAR(16) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_users_wechat_openid (wechat_openid),
  UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE servers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(32) NOT NULL,
  region VARCHAR(32),
  speed VARCHAR(16),
  start_date DATE,
  status VARCHAR(16) DEFAULT 'active',
  UNIQUE KEY uk_servers_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tribes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(16) NOT NULL,
  name VARCHAR(32) NOT NULL,
  UNIQUE KEY uk_tribes_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE alliances (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  server_id BIGINT NOT NULL,
  name VARCHAR(64) NOT NULL,
  tag VARCHAR(16) NOT NULL,
  description TEXT,
  created_by BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_alliances_server_tag (server_id, tag),
  KEY idx_alliances_server (server_id),
  CONSTRAINT fk_alliances_server FOREIGN KEY (server_id) REFERENCES servers (id),
  CONSTRAINT fk_alliances_creator FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE game_accounts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  server_id BIGINT NOT NULL,
  tribe_id INT NOT NULL,
  in_game_name VARCHAR(64) NOT NULL,
  status VARCHAR(16) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_accounts_server_name (server_id, in_game_name),
  KEY idx_accounts_user (user_id),
  KEY idx_accounts_server (server_id),
  KEY idx_accounts_tribe (tribe_id),
  CONSTRAINT fk_accounts_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_accounts_server FOREIGN KEY (server_id) REFERENCES servers (id),
  CONSTRAINT fk_accounts_tribe FOREIGN KEY (tribe_id) REFERENCES tribes (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE alliance_members (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alliance_id BIGINT NOT NULL,
  game_account_id BIGINT NOT NULL,
  server_id BIGINT NOT NULL,
  role VARCHAR(16) NOT NULL,
  join_status VARCHAR(16) DEFAULT 'pending',
  joined_at TIMESTAMP NULL,
  UNIQUE KEY uk_members_alliance_account (alliance_id, game_account_id),
  KEY idx_members_server (server_id),
  KEY idx_members_alliance (alliance_id),
  KEY idx_members_account (game_account_id),
  CONSTRAINT fk_members_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_members_account FOREIGN KEY (game_account_id) REFERENCES game_accounts (id),
  CONSTRAINT fk_members_server FOREIGN KEY (server_id) REFERENCES servers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invitations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alliance_id BIGINT NOT NULL,
  inviter_account_id BIGINT NOT NULL,
  invitee_user_id BIGINT,
  token VARCHAR(64) NOT NULL,
  status VARCHAR(16) DEFAULT 'pending',
  expires_at DATETIME,
  UNIQUE KEY uk_invitations_token (token),
  KEY idx_inv_alliance (alliance_id),
  KEY idx_inv_inviter (inviter_account_id),
  KEY idx_inv_invitee (invitee_user_id),
  CONSTRAINT fk_inv_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_inv_inviter FOREIGN KEY (inviter_account_id) REFERENCES game_accounts (id),
  CONSTRAINT fk_inv_invitee FOREIGN KEY (invitee_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE villages (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  server_id BIGINT NOT NULL,
  game_account_id BIGINT NOT NULL,
  name VARCHAR(64) NOT NULL,
  x INT NOT NULL,
  y INT NOT NULL,
  population INT DEFAULT 0,
  is_capital TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_villages_server_xy (server_id, x, y),
  KEY idx_villages_account (game_account_id),
  KEY idx_villages_server (server_id),
  CONSTRAINT fk_villages_server FOREIGN KEY (server_id) REFERENCES servers (id),
  CONSTRAINT fk_villages_account FOREIGN KEY (game_account_id) REFERENCES game_accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE troop_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tribe_id INT NOT NULL,
  code VARCHAR(16) NOT NULL,
  name VARCHAR(32) NOT NULL,
  UNIQUE KEY uk_troop_types_tribe_code (tribe_id, code),
  KEY idx_troop_types_tribe (tribe_id),
  CONSTRAINT fk_troop_types_tribe FOREIGN KEY (tribe_id) REFERENCES tribes (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE troop_counts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  village_id BIGINT NOT NULL,
  troop_type_id INT NOT NULL,
  count BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_troop_counts_village_type (village_id, troop_type_id),
  KEY idx_troop_counts_village (village_id),
  KEY idx_troop_counts_type (troop_type_id),
  CONSTRAINT fk_troop_counts_village FOREIGN KEY (village_id) REFERENCES villages (id),
  CONSTRAINT fk_troop_counts_type FOREIGN KEY (troop_type_id) REFERENCES troop_types (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE defense_requests (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alliance_id BIGINT NOT NULL,
  requester_account_id BIGINT NOT NULL,
  target_x INT NOT NULL,
  target_y INT NOT NULL,
  arrive_time DATETIME NOT NULL,
  needs_json JSON NOT NULL,
  status VARCHAR(16) DEFAULT 'open',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_def_req_alliance (alliance_id),
  KEY idx_def_req_requester (requester_account_id),
  CONSTRAINT fk_def_req_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_def_req_requester FOREIGN KEY (requester_account_id) REFERENCES game_accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE defense_assignments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  defense_request_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  from_village_id BIGINT,
  troop_type_id INT,
  count BIGINT,
  status VARCHAR(16) DEFAULT 'assigned',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_def_asn_request (defense_request_id),
  KEY idx_def_asn_account (account_id),
  KEY idx_def_asn_village (from_village_id),
  KEY idx_def_asn_type (troop_type_id),
  CONSTRAINT fk_def_asn_request FOREIGN KEY (defense_request_id) REFERENCES defense_requests (id),
  CONSTRAINT fk_def_asn_account FOREIGN KEY (account_id) REFERENCES game_accounts (id),
  CONSTRAINT fk_def_asn_village FOREIGN KEY (from_village_id) REFERENCES villages (id),
  CONSTRAINT fk_def_asn_type FOREIGN KEY (troop_type_id) REFERENCES troop_types (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE attack_plans (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alliance_id BIGINT NOT NULL,
  target_x INT NOT NULL,
  target_y INT NOT NULL,
  target_village_id BIGINT,
  start_time DATETIME NOT NULL,
  waves_json JSON NOT NULL,
  notes TEXT,
  status VARCHAR(16) DEFAULT 'planned',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_atk_plans_alliance (alliance_id),
  KEY idx_atk_plans_target_village (target_village_id),
  CONSTRAINT fk_atk_plans_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_atk_plans_target_village FOREIGN KEY (target_village_id) REFERENCES villages (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE attack_participants (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  attack_plan_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  from_village_id BIGINT,
  role VARCHAR(16) NOT NULL,
  troop_type_id INT,
  count BIGINT,
  landing_time DATETIME,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_atk_part_plan (attack_plan_id),
  KEY idx_atk_part_account (account_id),
  KEY idx_atk_part_village (from_village_id),
  KEY idx_atk_part_type (troop_type_id),
  CONSTRAINT fk_atk_part_plan FOREIGN KEY (attack_plan_id) REFERENCES attack_plans (id),
  CONSTRAINT fk_atk_part_account FOREIGN KEY (account_id) REFERENCES game_accounts (id),
  CONSTRAINT fk_atk_part_village FOREIGN KEY (from_village_id) REFERENCES villages (id),
  CONSTRAINT fk_atk_part_type FOREIGN KEY (troop_type_id) REFERENCES troop_types (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE resource_push_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alliance_id BIGINT NOT NULL,
  requester_village_id BIGINT NOT NULL,
  target_village_id BIGINT NOT NULL,
  resource_type VARCHAR(8) NOT NULL,
  amount BIGINT NOT NULL,
  arrive_time DATETIME NOT NULL,
  status VARCHAR(16) DEFAULT 'open',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_rpo_alliance (alliance_id),
  KEY idx_rpo_requester (requester_village_id),
  KEY idx_rpo_target (target_village_id),
  CONSTRAINT fk_rpo_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_rpo_requester FOREIGN KEY (requester_village_id) REFERENCES villages (id),
  CONSTRAINT fk_rpo_target FOREIGN KEY (target_village_id) REFERENCES villages (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE battle_reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  server_id BIGINT NOT NULL,
  alliance_id BIGINT,
  report_source VARCHAR(16) NOT NULL,
  text_raw MEDIUMTEXT NOT NULL,
  parsed_json JSON,
  reporter_account_id BIGINT NOT NULL,
  report_time DATETIME NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_reports_server (server_id),
  KEY idx_reports_alliance (alliance_id),
  KEY idx_reports_reporter (reporter_account_id),
  CONSTRAINT fk_reports_server FOREIGN KEY (server_id) REFERENCES servers (id),
  CONSTRAINT fk_reports_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id),
  CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_account_id) REFERENCES game_accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE files (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  owner_account_id BIGINT NOT NULL,
  alliance_id BIGINT,
  type VARCHAR(16) NOT NULL,
  oss_key VARCHAR(256) NOT NULL,
  url VARCHAR(512) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_files_owner (owner_account_id),
  KEY idx_files_alliance (alliance_id),
  CONSTRAINT fk_files_owner FOREIGN KEY (owner_account_id) REFERENCES game_accounts (id),
  CONSTRAINT fk_files_alliance FOREIGN KEY (alliance_id) REFERENCES alliances (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notifications (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  type VARCHAR(16) NOT NULL,
  channel VARCHAR(16) NOT NULL,
  payload_json JSON NOT NULL,
  delivered_at DATETIME,
  status VARCHAR(16) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_notif_user (user_id),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  actor_account_id BIGINT NOT NULL,
  action VARCHAR(32) NOT NULL,
  entity_type VARCHAR(32) NOT NULL,
  entity_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_audit_actor (actor_account_id),
  CONSTRAINT fk_audit_actor FOREIGN KEY (actor_account_id) REFERENCES game_accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;