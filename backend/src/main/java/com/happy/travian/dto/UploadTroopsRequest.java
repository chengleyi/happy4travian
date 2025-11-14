package com.happy.travian.dto;

import java.util.Map;

public class UploadTroopsRequest {
  private Long villageId;
  private Map<Integer, Long> counts;
  public Long getVillageId() { return villageId; }
  public void setVillageId(Long villageId) { this.villageId = villageId; }
  public Map<Integer, Long> getCounts() { return counts; }
  public void setCounts(Map<Integer, Long> counts) { this.counts = counts; }
}