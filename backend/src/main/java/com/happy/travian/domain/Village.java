package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "villages")
public class Village {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;
  @Column(name = "server_id", nullable = false)
  private Long serverId;
  @Column(name = "game_account_id", nullable = false)
  private Long gameAccountId;
  @Column(name = "name", nullable = false, length = 64)
  private String name;
  @Column(name = "x", nullable = false)
  private Integer x;
  @Column(name = "y", nullable = false)
  private Integer y;
  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public Long getServerId() { return serverId; }
  public void setServerId(Long serverId) { this.serverId = serverId; }
  public Long getGameAccountId() { return gameAccountId; }
  public void setGameAccountId(Long gameAccountId) { this.gameAccountId = gameAccountId; }
  public String getName() { return name; }
  public void setName(String name) { this.name = name; }
  public Integer getX() { return x; }
  public void setX(Integer x) { this.x = x; }
  public Integer getY() { return y; }
  public void setY(Integer y) { this.y = y; }
}