package com.happy.travian.repository;

import com.happy.travian.domain.Tribe;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TribeRepository extends JpaRepository<Tribe, Integer> { }