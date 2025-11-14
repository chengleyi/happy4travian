package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "troop_counts")
public class TroopCount {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;
  @Column(name = "village_id", nullable = false)
  private Long villageId;
  @Column(name = "troop_type_id", nullable = false)
  private Integer troopTypeId;
  @Column(name = "count", nullable = false)
  private Long count;
  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public Long getVillageId() { return villageId; }
  public void setVillageId(Long villageId) { this.villageId = villageId; }
  public Integer getTroopTypeId() { return troopTypeId; }
  public void setTroopTypeId(Integer troopTypeId) { this.troopTypeId = troopTypeId; }
  public Long getCount() { return count; }
  public void setCount(Long count) { this.count = count; }
}