#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def msg(mesg):
  print(':: BACKEND {}'.format(mesg))
  return

def msg_job_start(mesg):
  print(' ')
  print(' ')
  print('>> STARTING JOB {}'.format(mesg))
  return

def msg_job_done(mesg):
  print('>> JOB {} DONE'.format(mesg))
  print(' ')
  print(' ')
  return
