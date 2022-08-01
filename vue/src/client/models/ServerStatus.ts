/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type ServerStatus = {
  uptime: {
    iso8601: string;
    days: number;
    seconds: number;
    useconds: number;
  };
  hostname: string;
  ip: string;
};
