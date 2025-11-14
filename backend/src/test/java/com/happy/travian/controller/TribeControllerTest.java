package com.happy.travian.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class TribeControllerTest {
  @Autowired
  private TestRestTemplate rest;

  @Test
  void createAndList() {
    var body = "{\"code\":\"gauls\",\"name\":\"Gauls\"}";
    var headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_JSON);
    var resp = rest.postForEntity("/api/v1/tribes", new HttpEntity<>(body, headers), String.class);
    assertEquals(HttpStatus.OK, resp.getStatusCode());
    var list = rest.getForEntity("/api/v1/tribes", String.class);
    assertEquals(HttpStatus.OK, list.getStatusCode());
    assertTrue(list.getBody() != null && list.getBody().contains("gauls"));
  }
}