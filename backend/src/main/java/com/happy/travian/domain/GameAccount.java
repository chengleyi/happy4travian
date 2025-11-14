package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "game_accounts")
public class GameAccount {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;
  @Column(name = "user_id", nullable = false)
  private Long userId;
  @Column(name = "server_id", nullable = false)
  private Long serverId;
  @Column(name = "tribe_id", nullable = false)
  private Integer tribeId;
  @Column(name = "in_game_name", nullable = false, length = 64)
  private String inGameName;
  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public Long getUserId() { return userId; }
  public void setUserId(Long userId) { this.userId = userId; }
  public Long getServerId() { return serverId; }
  public void setServerId(Long serverId) { this.serverId = serverId; }
  public Integer getTribeId() { return tribeId; }
  public void setTribeId(Integer tribeId) { this.tribeId = tribeId; }
  public String getInGameName() { return inGameName; }
  public void setInGameName(String inGameName) { this.inGameName = inGameName; }
}