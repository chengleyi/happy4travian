package com.happy.travian.dto;

public class CreateVillageRequest {
  private Long serverId;
  private Long gameAccountId;
  private String name;
  private Integer x;
  private Integer y;
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