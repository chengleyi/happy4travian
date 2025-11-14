package com.happy.travian.dto;

public class CreateGameAccountRequest {
  private Long userId;
  private Long serverId;
  private Integer tribeId;
  private String inGameName;
  public Long getUserId() { return userId; }
  public void setUserId(Long userId) { this.userId = userId; }
  public Long getServerId() { return serverId; }
  public void setServerId(Long serverId) { this.serverId = serverId; }
  public Integer getTribeId() { return tribeId; }
  public void setTribeId(Integer tribeId) { this.tribeId = tribeId; }
  public String getInGameName() { return inGameName; }
  public void setInGameName(String inGameName) { this.inGameName = inGameName; }
}