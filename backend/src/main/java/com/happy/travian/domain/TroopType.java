package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "troop_types")
public class TroopType {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Integer id;
  @Column(name = "tribe_id", nullable = false)
  private Integer tribeId;
  @Column(name = "code", nullable = false, length = 16)
  private String code;
  @Column(name = "name", nullable = false, length = 32)
  private String name;
  public Integer getId() { return id; }
  public void setId(Integer id) { this.id = id; }
  public Integer getTribeId() { return tribeId; }
  public void setTribeId(Integer tribeId) { this.tribeId = tribeId; }
  public String getCode() { return code; }
  public void setCode(String code) { this.code = code; }
  public String getName() { return name; }
  public void setName(String name) { this.name = name; }
}